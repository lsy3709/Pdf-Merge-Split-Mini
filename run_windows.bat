@echo off
setlocal enableextensions enabledelayedexpansion

REM 한글 주석: 윈도우에서 한번에 실행 (venv 생성 → 의존성 설치 → 서버 실행)

REM 1) Python 실행기 감지
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

echo [INFO] Using Python launcher: %PY%
%PY% --version || (
  echo [ERROR] Python not found. Please install Python 3.9+.
  exit /b 1
)

REM 2) 가상환경 생성(없으면)
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment (.venv)
  %PY% -m venv .venv || (echo [ERROR] venv creation failed & exit /b 1)
)

REM 3) 가상환경 활성화
call ".venv\Scripts\activate.bat" || (echo [ERROR] venv activate failed & exit /b 1)

REM 4) 의존성 설치/업그레이드
echo [INFO] Upgrading pip and installing requirements
python -m pip install --upgrade pip setuptools wheel || (echo [ERROR] pip upgrade failed & exit /b 1)
python -m pip install -r requirements.txt || (echo [ERROR] requirements install failed & exit /b 1)

REM 5) 서버 실행 (app.py는 0.0.0.0:8000 고정, reload 미사용)
REM 5) 사용 가능한 포트 자동 선택 (8000~8010)
set PORT=
for /l %%P in (8000,1,8010) do (
  (netstat -ano | findstr LISTENING | findstr :%%P) >nul 2>&1
  if errorlevel 1 (
    set PORT=%%P
    goto :FOUND_PORT
  )
)
echo [ERROR] No free port in 8000..8010
exit /b 1

:FOUND_PORT
echo [INFO] Using port !PORT!

REM 6) Python 런처로 서버 실행/브라우저 오픈(내부에서 처리)
python launch.py

REM 참고: 8000 포트 문제가 있을 경우 아래를 수동으로 시도하세요
REM python -m uvicorn app:app --host 0.0.0.0 --port 8001 --lifespan off

endlocal

