from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader, PdfWriter

from .utils import (
	ensure_file_exists,
	ensure_output_directory_exists,
	assert_can_write,
	parse_ranges_to_groups,
)


def split_pdf_by_ranges(
	input_file: Path,
	output_dir: Path,
	ranges_text: Optional[str],
	overwrite: bool = False,
) -> List[Path]:
	"""
	PDF를 분할합니다.

	- ranges_text가 없으면 각 페이지를 개별 파일로 분할합니다.
	- ranges_text가 있으면 각 범위를 하나의 파일로 저장합니다.
	- 반환값: 생성된 출력 파일 경로 목록
	"""
	ensure_file_exists(input_file)

	reader = PdfReader(str(input_file))
	if getattr(reader, "is_encrypted", False):
		raise PermissionError(f"암호화된 PDF는 분할할 수 없습니다: {input_file}")

	total_pages = len(reader.pages)

	ensure_output_directory_exists(output_dir)

	basename = input_file.stem

	output_files: List[Path] = []

	if ranges_text is None:
		# 페이지별 파일 생성
		for page_index in range(total_pages):
			output_path = output_dir / f"{basename}_page_{page_index + 1}.pdf"
			assert_can_write(output_path, overwrite)

			writer = PdfWriter()
			writer.add_page(reader.pages[page_index])
			with output_path.open("wb") as f_out:
				writer.write(f_out)

			output_files.append(output_path)
		return output_files

	# 범위별 파일 생성
	groups = parse_ranges_to_groups(ranges_text, total_pages)
	if len(groups) == 0:
		return []

	for group_index, page_group in enumerate(groups, start=1):
		output_path = output_dir / f"{basename}_part_{group_index}.pdf"
		assert_can_write(output_path, overwrite)

		writer = PdfWriter()
		for page_index in page_group:
			writer.add_page(reader.pages[page_index])
		with output_path.open("wb") as f_out:
			writer.write(f_out)
		output_files.append(output_path)

	return output_files
