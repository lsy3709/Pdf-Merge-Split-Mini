from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from pypdf import PdfReader
from starlette.testclient import TestClient

# 한글 주석: FastAPI 앱을 직접 임포트하여 실제 HTTP 요청 시뮬레이션
from app import app


def get_page_count(pdf_path: Path) -> int:
	"""PDF 페이지 수를 반환합니다."""
	reader = PdfReader(str(pdf_path))
	return len(reader.pages)


def save_bytes(output_path: Path, data: bytes) -> None:
	"""바이트 데이터를 파일로 저장합니다."""
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("wb") as f_out:
		f_out.write(data)


def http_split_test(client: TestClient, pdf_path: Path, ranges: Optional[str]) -> Path:
	"""
	/split 엔드포인트 테스트. 응답을 파일로 저장하고 경로 반환.
	- ranges가 None이면 각 페이지를 개별 PDF로 생성하므로 ZIP이 내려옵니다.
	- ranges가 지정되면 하나의 PDF 또는 ZIP이 내려옵니다(구간 개수에 따라).
	"""
	files = {"file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")}
	data = {}
	if ranges is not None:
		data["ranges"] = ranges

	resp = client.post("/split", files=files, data=data)
	if not (200 <= resp.status_code < 400):
		raise RuntimeError(f"/split 실패: status={resp.status_code}, body={resp.text}")

	content_type = resp.headers.get("content-type", "")
	if content_type.startswith("application/pdf"):
		out_path = Path("test_outputs/split_result.pdf")
	else:
		out_path = Path("test_outputs/split_result.zip")

	save_bytes(out_path, resp.content)
	return out_path


def http_merge_test(client: TestClient, pdf_path: Path) -> Path:
	"""/merge 엔드포인트 테스트. 같은 파일 2개를 업로드하여 병합 결과를 저장합니다."""
	files = [
		("files", (pdf_path.name, pdf_path.read_bytes(), "application/pdf")),
		("files", (pdf_path.name, pdf_path.read_bytes(), "application/pdf")),
	]
	data = {"output_name": "merged_test.pdf"}
	resp = client.post("/merge", files=files, data=data)
	if not (200 <= resp.status_code < 400):
		raise RuntimeError(f"/merge 실패: status={resp.status_code}, body={resp.text}")

	out_path = Path("test_outputs/merged_test.pdf")
	save_bytes(out_path, resp.content)
	return out_path


def main() -> None:
	if len(sys.argv) < 2:
		print("사용법: python run_tests.py <PDF 경로>")
		sys.exit(2)

	pdf_path = Path(sys.argv[1]).resolve()
	if not pdf_path.exists():
		print(f"파일을 찾을 수 없습니다: {pdf_path}")
		sys.exit(1)

	# 1) 페이지 수 확인
	page_count = get_page_count(pdf_path)
	print(f"PAGE_COUNT {page_count}")

	# 2) 앱 클라이언트 준비
	client = TestClient(app)

	# 3) 분할 테스트: 페이지가 21 이상이면 1-21, 아니면 전체(빈 ranges)
	if page_count >= 21:
		split_out = http_split_test(client, pdf_path, ranges="1-21")
	else:
		split_out = http_split_test(client, pdf_path, ranges=None)
	print(f"SPLIT_SAVED {split_out}")

	# 4) 병합 테스트: 같은 파일 2개 업로드
	merge_out = http_merge_test(client, pdf_path)
	print(f"MERGE_SAVED {merge_out}")


if __name__ == "__main__":
	main()


