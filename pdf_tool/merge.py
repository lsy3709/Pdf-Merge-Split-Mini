from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from pypdf import PdfReader, PdfWriter

from .utils import ensure_file_exists, ensure_output_directory_exists, assert_can_write


def merge_pdfs(input_files: Iterable[Path], output_file: Path, overwrite: bool = False) -> None:
	"""
	여러 PDF 파일을 순서대로 병합합니다.

	- 입력 파일은 2개 이상이어야 합니다.
	- 이미 존재하는 출력 파일은 --overwrite 옵션이 없으면 덮어쓰지 않습니다.
	"""
	# 입력 목록 전처리 및 검증
	input_paths: List[Path] = [Path(p) for p in input_files]
	if len(input_paths) < 2:
		raise ValueError("병합에는 최소 2개의 입력 파일이 필요합니다.")

	for path in input_paths:
		ensure_file_exists(path)

	ensure_output_directory_exists(output_file)
	assert_can_write(output_file, overwrite)

	writer = PdfWriter()

	for path in input_paths:
		reader = PdfReader(str(path))

		# 암호화된 파일은 처리하지 않음
		if getattr(reader, "is_encrypted", False):
			raise PermissionError(f"암호화된 PDF는 병합할 수 없습니다: {path}")

		for page in reader.pages:
			writer.add_page(page)

	with output_file.open("wb") as f_out:
		writer.write(f_out)
