# YouTube 다운로더 설정

## 기본 다운로드 경로
BASE_DOWNLOAD_PATH = r"D:\ftp\minjung"

## 서버 설정
HOST = "0.0.0.0"  # 모든 네트워크 인터페이스에서 접속 허용
PORT = 8000

## yt-dlp 기본 옵션
DEFAULT_VIDEO_FORMAT = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
DEFAULT_AUDIO_QUALITY = "192"  # kbps

## 파일명 템플릿
VIDEO_TEMPLATE = "%(title)s.%(ext)s"
CHANNEL_TEMPLATE = "%(playlist_index)s_%(title)s.%(ext)s"
