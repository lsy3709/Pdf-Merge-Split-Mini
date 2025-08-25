from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader, PdfWriter
from zipfile import ZipFile, ZIP_DEFLATED

from pdf_tool.utils import parse_ranges_to_groups

app = FastAPI(title="PDF 병합/분할 웹")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
	# 간단한 업로드 UI 렌더링
	return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
	return {"status": "ok"}


@app.post("/merge")
async def merge_endpoint(
	files: List[UploadFile] = File(..., description="병합할 PDF 파일들 (2개 이상)"),
	output_name: str = Form(default="merged.pdf"),
):
	# 입력 검증: 최소 2개 파일
	if files is None or len(files) < 2:
		raise HTTPException(status_code=400, detail="병합에는 최소 2개의 PDF가 필요합니다.")

	writer = PdfWriter()

	for upload in files:
		# 파일명 검증 (정보용)
		if not upload.filename or not upload.filename.lower().endswith(".pdf"):
			raise HTTPException(status_code=400, detail=f"PDF 파일만 업로드하세요: {upload.filename}")
		data = await upload.read()
		if not data:
			raise HTTPException(status_code=400, detail=f"빈 파일입니다: {upload.filename}")
		try:
			reader = PdfReader(BytesIO(data))
		except Exception:
			raise HTTPException(status_code=400, detail=f"유효하지 않은 PDF입니다: {upload.filename}")

		if getattr(reader, "is_encrypted", False):
			raise HTTPException(status_code=400, detail=f"암호화된 PDF는 병합할 수 없습니다: {upload.filename}")

		for page in reader.pages:
			writer.add_page(page)

	# 출력 이름 보정
	safe_name = output_name.strip() or "merged.pdf"
	if not safe_name.lower().endswith(".pdf"):
		safe_name += ".pdf"

	out_buf = BytesIO()
	writer.write(out_buf)
	out_buf.seek(0)

	return StreamingResponse(
		out_buf,
		media_type="application/pdf",
		headers={
			"Content-Disposition": f"attachment; filename=\"{safe_name}\""
		},
	)


@app.post("/split")
async def split_endpoint(
	file: UploadFile = File(..., description="분할할 PDF 파일"),
	ranges: Optional[str] = Form(default=None, description="예: 1-3,5,7-"),
):
	# 입력 파일 검증
	if not file.filename or not file.filename.lower().endswith(".pdf"):
		raise HTTPException(status_code=400, detail=f"PDF 파일만 업로드하세요: {file.filename}")

	data = await file.read()
	if not data:
		raise HTTPException(status_code=400, detail="빈 파일입니다.")
	try:
		reader = PdfReader(BytesIO(data))
	except Exception:
		raise HTTPException(status_code=400, detail="유효하지 않은 PDF입니다.")

	if getattr(reader, "is_encrypted", False):
		raise HTTPException(status_code=400, detail="암호화된 PDF는 분할할 수 없습니다.")

	total_pages = len(reader.pages)
	base_name = (Path(file.filename).stem or "document").replace("\"", "_")

	# ranges가 없으면 각 페이지별 파일 생성
	def build_single_pdf(pages: List[int]) -> bytes:
		writer = PdfWriter()
		for idx in pages:
			writer.add_page(reader.pages[idx])
		buf = BytesIO()
		writer.write(buf)
		return buf.getvalue()

	outputs: List[tuple[str, bytes]] = []

	if ranges is None or ranges.strip() == "":
		for i in range(total_pages):
			pdf_bytes = build_single_pdf([i])
			outputs.append((f"{base_name}_page_{i + 1}.pdf", pdf_bytes))
	else:
		# 범위 파싱 (1-기반 입력을 0-기반 인덱스로 변환)
		try:
			groups = parse_ranges_to_groups(ranges.strip(), total_pages)
		except Exception as e:
			raise HTTPException(status_code=400, detail=str(e))

		for gi, group in enumerate(groups, start=1):
			pdf_bytes = build_single_pdf(group)
			outputs.append((f"{base_name}_part_{gi}.pdf", pdf_bytes))

	# 응답: 1개면 PDF 그대로, 여러 개면 ZIP
	if len(outputs) == 0:
		raise HTTPException(status_code=500, detail="생성된 파일이 없습니다.")

	if len(outputs) == 1:
		name, data_bytes = outputs[0]
		return StreamingResponse(
			BytesIO(data_bytes),
			media_type="application/pdf",
			headers={"Content-Disposition": f"attachment; filename=\"{name}\""},
		)

	zip_buf = BytesIO()
	with ZipFile(zip_buf, mode="w", compression=ZIP_DEFLATED) as zf:
		for name, data_bytes in outputs:
			zf.writestr(name, data_bytes)
	zip_buf.seek(0)

	zip_name = f"{base_name}_split.zip"
	return StreamingResponse(
		zip_buf,
		media_type="application/zip",
		headers={"Content-Disposition": f"attachment; filename=\"{zip_name}\""},
	)
