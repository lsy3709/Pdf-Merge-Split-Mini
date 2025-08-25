from __future__ import annotations

from pathlib import Path
from typing import List


def ensure_file_exists(file_path: Path) -> None:
	"""
	입력 파일 존재 여부를 확인하고, 없으면 예외를 발생시킵니다.
	"""
	# 파일 존재 확인 (한국어 에러 메시지)
	if not file_path.exists() or not file_path.is_file():
		raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")


def ensure_output_directory_exists(output_path: Path) -> None:
	"""
	출력 경로의 상위 디렉터리를 생성합니다. 파일이면 부모 디렉터리, 디렉터리면 그대로 생성.
	"""
	parent = output_path if output_path.suffix == "" else output_path.parent
	parent.mkdir(parents=True, exist_ok=True)


def assert_can_write(output_path: Path, overwrite: bool) -> None:
	"""
	출력 경로에 쓸 수 있는지 확인합니다. 이미 존재하면 overwrite가 필요합니다.
	"""
	if output_path.exists() and not overwrite:
		raise FileExistsError(
			f"이미 파일이 존재합니다. --overwrite 옵션을 사용하세요: {output_path}"
		)


def parse_ranges_to_groups(ranges_text: str, total_pages: int) -> List[List[int]]:
	"""
	"1-3,5,7-" 같은 범위 문자열을 0-기반 인덱스의 그룹 목록으로 변환합니다.

	- 입력은 1-기반 페이지 번호 기준입니다.
	- 각 쉼표 구분 토큰은 하나의 그룹이 되며, 그룹별로 별도 파일을 생성할 때 사용됩니다.
	- 열린 구간 "A-"는 A부터 끝까지를 의미합니다.

	예)
	"1-3,5,7-" -> [[0,1,2], [4], [6,7,8,...]]
	"""
	# 입력 검증 및 전처리
	if not ranges_text or ranges_text.strip() == "":
		raise ValueError("범위 문자열이 비어 있습니다.")

	tokens = [t.strip() for t in ranges_text.split(",") if t.strip() != ""]
	if len(tokens) == 0:
		raise ValueError("유효한 범위 토큰이 없습니다.")

	groups: List[List[int]] = []

	for token in tokens:
		start_end = token.split("-")

		# 단일 페이지 토큰 (예: "5")
		if len(start_end) == 1:
			page_1_based = _parse_positive_int(start_end[0])
			_assert_in_range(page_1_based, 1, total_pages)
			groups.append([page_1_based - 1])
			continue

		# 구간 토큰 (예: "1-3", "7-")
		if len(start_end) == 2:
			start_text, end_text = start_end[0].strip(), start_end[1].strip()

			if start_text == "":
				raise ValueError(f"잘못된 범위입니다: '{token}' (시작 페이지 필요)")

			start_1_based = _parse_positive_int(start_text)
			_assert_in_range(start_1_based, 1, total_pages)

			# 열린 구간: "A-"
			if end_text == "":
				start_index = start_1_based - 1
				end_index = total_pages - 1
				groups.append(list(range(start_index, end_index + 1)))
				continue

			# 닫힌 구간: "A-B"
			end_1_based = _parse_positive_int(end_text)
			_assert_in_range(end_1_based, 1, total_pages)

			if end_1_based < start_1_based:
				raise ValueError(f"잘못된 범위입니다(끝 < 시작): '{token}'")

			start_index = start_1_based - 1
			end_index = end_1_based - 1
			groups.append(list(range(start_index, end_index + 1)))
			continue

		raise ValueError(f"잘못된 범위 토큰입니다: '{token}'")

	return groups


def _parse_positive_int(text: str) -> int:
	"""
	양의 정수를 파싱합니다. 실패 시 예외를 발생시킵니다.
	"""
	try:
		value = int(text)
	except Exception:
		raise ValueError(f"숫자를 파싱할 수 없습니다: '{text}'")

	if value <= 0:
		raise ValueError(f"양의 정수만 허용됩니다: '{text}'")

	return value


def _assert_in_range(value_1_based: int, min_1_based: int, max_1_based: int) -> None:
	"""
	1-기반 값이 지정한 범위에 있는지 확인합니다.
	"""
	if not (min_1_based <= value_1_based <= max_1_based):
		raise ValueError(
			f"페이지 번호가 범위를 벗어났습니다: {value_1_based} (허용: {min_1_based}~{max_1_based})"
		)
