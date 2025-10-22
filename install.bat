@echo off
echo ========================================
echo YouTube 다운로더 설치 및 실행 가이드
echo ========================================
echo.

echo 1단계: Python 설치 확인
echo -----------------------------------
python --version 2>nul
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다!
    echo.
    echo Python 3.8 이상을 설치해주세요:
    echo https://www.python.org/downloads/
    echo.
    echo 설치 시 "Add Python to PATH" 옵션을 꼭 체크하세요!
    echo.
    pause
    exit /b 1
) else (
    echo [성공] Python이 설치되어 있습니다.
)
echo.

echo 2단계: 필요한 패키지 설치
echo -----------------------------------
echo 패키지 설치 중...
pip install -r requirements.txt
if errorlevel 1 (
    echo [오류] 패키지 설치 실패
    pause
    exit /b 1
)
echo [성공] 모든 패키지가 설치되었습니다.
echo.

echo 3단계: FFmpeg 확인
echo -----------------------------------
ffmpeg -version 2>nul
if errorlevel 1 (
    echo [경고] FFmpeg가 설치되어 있지 않습니다.
    echo MP3 변환 기능을 사용하려면 FFmpeg를 설치해야 합니다.
    echo.
    echo 설치 방법:
    echo - Chocolatey 사용: choco install ffmpeg
    echo - 수동 설치: https://www.gyan.dev/ffmpeg/builds/
    echo.
) else (
    echo [성공] FFmpeg가 설치되어 있습니다.
)
echo.

echo 4단계: 다운로드 폴더 확인
echo -----------------------------------
if not exist "D:\ftp\minjung" (
    echo D:\ftp\minjung 폴더 생성 중...
    mkdir "D:\ftp\minjung" 2>nul
    if errorlevel 1 (
        echo [경고] 폴더 생성 실패. 권한을 확인하세요.
    ) else (
        echo [성공] 폴더가 생성되었습니다.
    )
) else (
    echo [성공] 다운로드 폴더가 존재합니다.
)
echo.

echo ========================================
echo 설치가 완료되었습니다!
echo ========================================
echo.
echo 서버를 시작하려면 start.bat를 실행하세요.
echo.
pause
