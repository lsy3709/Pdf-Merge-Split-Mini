## PDF 병합/분할 도구 (CLI + Web)

간단한 명령행과 웹 UI로 PDF를 병합하거나 분할합니다. 내부적으로 `pypdf`를 사용합니다.

### 주요 기능

- **병합**: 여러 PDF를 순서대로 하나의 PDF로 합치기
- **분할**: 각 페이지별 분할 또는 범위 지정 분할
- **웹 UI**: 업로드/다운로드 중심의 간단한 화면 제공
- **순서 지정 병합 UI**: 프론트에서 드래그로 순서를 정하고 그 순서대로 병합

### 요구사항

- Python 3.9+
- OS: Windows, macOS, Linux

### 설치

```bash
pip install -r requirements.txt
```

Windows에서 Python이 `py` 런처로 등록된 경우:

```bash
py -m pip install -r requirements.txt
```

### 빠른 시작

- CLI 병합: `python main.py merge -i a.pdf b.pdf -o merged.pdf`
- CLI 분할(각 페이지): `python main.py split -i input.pdf -o out_dir`
- 웹 UI 실행(안정): `python app.py` 또는 `uvicorn app:app --host 0.0.0.0 --port 8000 --lifespan off`
  - 브라우저에서 `http://localhost:8000`

## 사용법 (CLI)

### 병합

```bash
python main.py merge -i a.pdf b.pdf c.pdf -o merged.pdf [--overwrite]
```

- **-i/--inputs**: 병합할 PDF 파일 경로들 (2개 이상)
- **-o/--output**: 출력 PDF 경로
- **--overwrite**: 출력 경로가 이미 있어도 덮어쓰기

### 분할

```bash
python main.py split -i input.pdf -o out_dir [-r "1-3,5,7-"] [--overwrite]
```

- 기본값: 각 페이지를 개별 PDF(`{basename}_page_{n}.pdf`)로 저장
- **-r/--ranges**: 1부터 시작하는 페이지 기준의 범위 표현
  - 예: `1-3`(1~3페이지), `5`(5페이지만), `7-`(7페이지부터 끝까지)
  - 쉼표로 여러 구간을 나열하면 각 구간별로 별도 파일 생성 (`{basename}_part_{idx}.pdf`)
- **--overwrite**: 출력 경로/파일이 이미 있어도 덮어쓰기

## 사용법 (웹 UI)

FastAPI + Uvicorn 기반의 간단한 웹 UI를 제공합니다.

```bash
python app.py
# 또는
uvicorn app:app --host 0.0.0.0 --port 8000 --lifespan off
```

브라우저에서 `http://localhost:8000` 접속 후:

- **병합**: "PDF 파일 추가" → 목록에서 드래그로 순서 조정 → 출력 파일명 입력 → "병합 실행"
- **분할**: PDF 업로드, 선택적으로 범위(예: `1-3,5,7-`) 입력 → 제출
  - 응답은 한 개면 PDF, 여러 개면 ZIP으로 다운로드됩니다.

## HTTP API (프로그램 연동)

### POST /merge

- Form fields
  - `files`: PDF 파일들 (2개 이상, multipart, 다중). 전송된 순서대로 병합됨
  - `output_name`: 출력 파일명 (기본: `merged.pdf`)
- Response: `application/pdf` (첨부 다운로드)

예시(cURL):

```bash
curl -X POST http://localhost:8000/merge \
  -F "files=@a.pdf" -F "files=@b.pdf" -F "output_name=merged.pdf" \
  -o merged.pdf
```

### POST /split

- Form fields
  - `file`: 분할할 PDF 파일 (단일)
  - `ranges`: 선택, 예 `1-3,5,7-`
- Response: 한 개면 `application/pdf`, 여러 개면 `application/zip`

예시(cURL):

```bash
curl -X POST http://localhost:8000/split \
  -F "file=@input.pdf" -F "ranges=1-3,5,7-" \
  -o output.zip
```

## 범위 표현 상세

- `N` → N 페이지만 포함 (1-기반)
- `A-B` → A~B 페이지 포함 (A ≤ B)
- `A-` → A페이지부터 끝까지 포함
- 쉼표로 구분된 각 토큰이 하나의 **그룹(파일)** 이 됩니다.

## 프로젝트 구조

```
pdf-program/
├─ main.py               # CLI 진입점
├─ app.py                # FastAPI 앱 (웹 UI/엔드포인트)
├─ pdf_tool/
│  ├─ merge.py          # 병합 로직
│  ├─ split.py          # 분할 로직
│  └─ utils.py          # 공용 유틸(검증/범위 파싱 등)
├─ templates/
│  └─ index.html        # 업로드 UI (병합 순서 지정 포함)
├─ run_tests.py          # 로컬에서 앱 엔드포인트 테스트 스크립트
├─ bind_test.py          # 포트 바인딩 진단 스크립트(Windows)
├─ requirements.txt
└─ README.md
```

## 문제 해결(FAQ)

- **암호화된 PDF 에러**: 열람/복사 제한이 있는 경우 처리되지 않습니다. 암호 해제 후 시도하세요.
- **이미 파일이 존재합니다 에러**: `--overwrite` 옵션을 사용하거나 다른 출력 경로를 지정하세요.
- **범위 오류(400)**: `1`부터 시작하고, 존재하는 페이지 내에서 `A ≤ B`를 만족해야 합니다. 예: `2-5,7,10-`.
- **Windows [WinError 10013] (127.0.0.1:8000 바인딩 실패)**: `--host 0.0.0.0` 사용 또는 다른 포트 사용.
- **reloader로 pypdf 모듈 오류**: `python app.py`로 실행하거나 `--reload` 미사용 권장.

## 개발

- 서버 실행(안정): `python app.py`
- 대안: `uvicorn app:app --host 0.0.0.0 --port 8000 --lifespan off`
- 테스트: `python run_tests.py <PDF 경로>`
- 코드 스타일: 타입 힌트/명확한 변수명/한국어 예외 메시지 유지

## 라이선스

MIT
