from __future__ import annotations

from pathlib import Path
from pypdf import PdfWriter


def create_simple_pdf(output_path: Path) -> None:
	writer = PdfWriter()
	# A4 크기의 빈 페이지 추가 (단위: pt)
	writer.add_blank_page(width=595, height=842)
	with output_path.open("wb") as f_out:
		writer.write(f_out)


def main() -> None:
	out_path = Path("test.pdf")
	create_simple_pdf(out_path)
	print(f"WROTE {out_path.resolve()}")


if __name__ == "__main__":
	main()


