@echo off
setlocal enableextensions enabledelayedexpansion

REM 한글 주석: uvicorn 또는 app.py로 띄운 서버 종료 스크립트

echo [INFO] Stopping server on common ports (8000..8010)
for /l %%P in (8000,1,8010) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr LISTENING ^| findstr :%%P') do (
    echo [INFO] Killing PID %%A on port %%P
    taskkill /PID %%A /F >nul 2>&1
  )
)

REM uvicorn/app.py 잔여 프로세스 정리 (주의: 다른 python 작업 종료될 수 있음)
REM 필요 시 주석 해제
REM taskkill /IM uvicorn.exe /F >nul 2>&1
REM taskkill /IM python.exe /F >nul 2>&1

echo [INFO] Done.
endlocal

