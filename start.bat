@echo off
echo ========================================
echo YouTube 다운로더 서버 시작
echo ========================================
echo.

C:\Python314\python.exe --version 2>nul
if errorlevel 1 (
    python --version 2>nul
    if errorlevel 1 (
        echo [오류] Python이 설치되어 있지 않습니다!
        echo install.bat를 먼저 실행하세요.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=C:\Python314\python.exe
)

echo 서버 시작 중...
echo.
echo 접속 주소:
echo - 로컬: http://localhost:8000
echo - 네트워크: http://서버IP:8000
echo.
echo 서버를 종료하려면 Ctrl+C를 누르세요.
echo.
echo ========================================
echo.

%PYTHON_CMD% main.py
