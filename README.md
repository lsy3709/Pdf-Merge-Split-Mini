# PDF 병합/분할 CLI (Python)

간단한 명령행 인터페이스로 PDF를 병합하고 분할합니다.

## 설치

```bash
pip install -r requirements.txt
```

Windows에서 Python이 `py` 런처로 등록된 경우:

```bash
py -m pip install -r requirements.txt
```

## 사용법 (CLI)

### 1) 병합

```bash
python main.py merge -i a.pdf b.pdf c.pdf -o merged.pdf
```

- `-i/--inputs`: 병합할 PDF 파일 경로들 (2개 이상)
- `-o/--output`: 출력 PDF 경로
- `--overwrite`: 출력 경로가 이미 있어도 덮어쓰기

### 2) 분할

```bash
python main.py split -i input.pdf -o out_dir
```

- 기본값: 각 페이지를 개별 PDF(`{basename}_page_{n}.pdf`)로 저장

범위를 지정하여 묶음 분할도 가능합니다:

```bash
python main.py split -i input.pdf -o out_dir -r "1-3,5,7-"
```

- `-r/--ranges`: 1부터 시작하는 페이지 기준의 범위 표현
  - 예: `1-3`(1~3페이지), `5`(5페이지만), `7-`(7페이지부터 끝까지)
  - 쉼표로 여러 구간을 나열하면 각 구간별로 별도 파일 생성 (`{basename}_part_{idx}.pdf`)
- `--overwrite`: 출력 파일이 이미 있어도 덮어쓰기

## 사용법 (웹)

FastAPI + Uvicorn 기반의 간단한 웹 UI를 제공합니다.

```bash
uvicorn app:app --reload --port 8000
```

브라우저에서 `http://localhost:8000` 접속 후:

- 병합: 여러 PDF 업로드 후 출력 파일명 입력 → 제출
- 분할: PDF 업로드, 선택적으로 범위(예: `1-3,5,7-`) 입력 → 제출

응답은 한 개면 PDF, 여러 개면 ZIP으로 다운로드됩니다.

## 주의사항

- 암호화된 PDF(열람/복사 제한 포함)는 처리에 실패할 수 있습니다.
- 잘못된 범위나 존재하지 않는 파일은 즉시 에러로 안내합니다.

## 라이선스

MIT
"# Pdf-Merge-Split-Mini" 
