from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from pdf_tool.merge import merge_pdfs
from pdf_tool.split import split_pdf_by_ranges


# 한글 도움말과 명확한 옵션명을 제공합니다.

def build_parser() -> argparse.ArgumentParser:
	"""
	최상위 인자 파서를 구성합니다.
	"""
	parser = argparse.ArgumentParser(
		prog="pdf-tool",
		description="PDF 병합/분할 도구",
	)

	subparsers = parser.add_subparsers(dest="command", required=True)

	# merge 서브커맨드
	merge_parser = subparsers.add_parser("merge", help="여러 PDF를 하나로 병합")
	merge_parser.add_argument(
		"-i",
		"--inputs",
		nargs='+',
		required=True,
		help="병합할 PDF 경로들 (2개 이상)",
	)
	merge_parser.add_argument(
		"-o",
		"--output",
		required=True,
		help="출력 PDF 경로",
	)
	merge_parser.add_argument(
		"--overwrite",
		action="store_true",
		help="출력 파일이 이미 있어도 덮어쓰기",
	)

	# split 서브커맨드
	split_parser = subparsers.add_parser("split", help="PDF를 페이지/범위로 분할")
	split_parser.add_argument(
		"-i",
		"--input",
		required=True,
		help="입력 PDF 경로",
	)
	split_parser.add_argument(
		"-o",
		"--output-dir",
		required=True,
		help="출력 디렉터리",
	)
	split_parser.add_argument(
		"-r",
		"--ranges",
		required=False,
		help="분할 범위 (예: '1-3,5,7-'). 생략 시 각 페이지별로 분할",
	)
	split_parser.add_argument(
		"--overwrite",
		action="store_true",
		help="출력 파일이 이미 있어도 덮어쓰기",
	)

	return parser


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()

	if args.command == "merge":
		input_paths: List[Path] = [Path(p) for p in args.inputs]
		output_path = Path(args.output)
		merge_pdfs(input_paths, output_path, overwrite=args.overwrite)
		print(f"병합 완료: {output_path}")
		return

	if args.command == "split":
		input_path = Path(args.input)
		output_dir = Path(args.output_dir)
		outputs = split_pdf_by_ranges(
			input_path,
			output_dir,
			ranges_text=args.ranges,
			overwrite=args.overwrite,
		)
		if len(outputs) == 0:
			print("생성된 파일이 없습니다.")
		else:
			print(f"분할 완료: {len(outputs)}개 파일 생성 → {output_dir}")
		return


if __name__ == "__main__":
	main()
