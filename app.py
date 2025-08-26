from __future__ import annotations

from io import BytesIO
from urllib.parse import quote as url_quote
from pathlib import Path
from typing import List, Optional
import os
import threading

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader, PdfWriter
from zipfile import ZipFile, ZIP_DEFLATED

from pdf_tool.utils import parse_ranges_to_groups

app = FastAPI(title="PDF 병합/분할 웹")

templates = Jinja2Templates(directory="templates")


def build_content_disposition(filename: str) -> str:
	"""다운로드 파일명을 위한 Content-Disposition 생성 (RFC 5987 지원).

	- ASCII fallback + filename* (UTF-8) 동시 제공
	- 따옴표/세미콜론 등 문제 문자는 밑줄로 치환
	"""
	fallback = "".join(
		ch if (0x20 <= ord(ch) < 0x7F and ch not in {'\\', '"', ';'}) else "_"
		for ch in filename
	)
	utf8_star = url_quote(filename, safe="")
	return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{utf8_star}"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
	"""간단한 업로드 UI를 렌더링합니다."""
	# 간단한 업로드 UI 렌더링
	return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
	"""헬스 체크 엔드포인트."""
	return {"status": "ok"}


@app.post("/merge")
async def merge_endpoint(
	files: List[UploadFile] = File(..., description="병합할 PDF 파일들 (2개 이상)"),
	output_name: str = Form(default="merged.pdf"),
):
	"""여러 PDF 파일을 병합하여 하나의 PDF로 스트리밍 반환합니다.

	- 파일 수가 2개 이상이어야 합니다.
	- 암호화된 PDF는 거부됩니다.
	- `output_name`은 비어 있으면 기본값으로 대체되며 확장자가 없으면 `.pdf`를 붙입니다.
	"""
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
			"Content-Disposition": build_content_disposition(safe_name)
		},
	)


@app.post("/admin/shutdown")
async def admin_shutdown(token: str = Form(...)):
	"""서버를 안전하게 종료합니다(개발용). 토큰이 일치해야 합니다.

	- 기본 토큰: "localdev". 운영 시 환경변수 ADMIN_TOKEN으로 변경하세요.
	"""
	admin_token = os.environ.get("ADMIN_TOKEN", "localdev")
	if token != admin_token:
		raise HTTPException(status_code=403, detail="유효하지 않은 토큰입니다.")
	# 응답을 보낸 뒤 프로세스를 종료합니다.
	threading.Timer(0.5, lambda: os._exit(0)).start()
	return {"ok": True, "message": "서버 종료를 요청했습니다."}


@app.post("/split")
async def split_endpoint(
	file: UploadFile = File(..., description="분할할 PDF 파일"),
	ranges: Optional[str] = Form(default=None, description="예: 1-3,5,7-"),
):
	"""PDF를 페이지별 또는 범위별로 분할하여 PDF/ZIP으로 반환합니다.

	- `ranges`가 비어 있으면 각 페이지를 개별 PDF로 생성합니다.
	- `ranges`가 지정되면 각 토큰별 그룹으로 파일을 생성합니다.
	- 암호화된 PDF는 거부됩니다.
	"""
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
		# 요청이 유효하나 결과가 비어있는 경우 400으로 응답
		raise HTTPException(status_code=400, detail="생성된 파일이 없습니다. 범위를 확인하세요.")

	if len(outputs) == 1:
		name, data_bytes = outputs[0]
		return StreamingResponse(
			BytesIO(data_bytes),
			media_type="application/pdf",
			headers={"Content-Disposition": build_content_disposition(name)},
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
		headers={"Content-Disposition": build_content_disposition(zip_name)},
	)


if __name__ == "__main__":
	"""개발 편의를 위한 직접 실행 엔트리.

	- 현재 파이썬 해석기에서 uvicorn을 사용해 서버를 기동합니다.
	- 문자열 경로 대신 앱 객체를 직접 전달해 재-import 이슈를 회피합니다.
	- 윈도우에서 reloader로 인한 해석기 차이 문제를 피하기 위해 reload=False.
	"""
	import uvicorn

	uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
