# YouTube 다운로더

FastAPI와 yt-dlp를 사용한 YouTube 비디오/오디오 다운로더입니다.

## 기능

- 🎬 **영상 다운로드 (MP4)**: 개별 YouTube 영상을 MP4 형식으로 다운로드
- 🎵 **영상을 MP3로 다운로드**: 개별 YouTube 영상의 오디오를 MP3로 추출
- 📺 **채널 전체 다운로드 (MP4)**: YouTube 채널 또는 재생목록의 모든 영상을 MP4로 다운로드
- 🎼 **채널을 MP3로 다운로드**: YouTube 채널 또는 재생목록의 모든 영상을 MP3로 변환

## 설치 방법

1. Python 3.8 이상 필요
2. 의존성 설치:
```bash
pip install -r requirements.txt
```

3. FFmpeg 설치 (MP3 변환을 위해 필요):
   - Windows: https://www.gyan.dev/ffmpeg/builds/ 에서 다운로드 후 PATH 추가
   - 또는 `choco install ffmpeg` (Chocolatey 사용 시)

## 실행 방법

```bash
python main.py
```

서버가 시작되면 다음 주소로 접속:
- **웹 인터페이스**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 다운로드 경로

모든 파일은 `D:\ftp\minjung` 경로에 다음 형식으로 저장됩니다:
- `YYYYMMDD_HHMMSS_video/` - 개별 영상
- `YYYYMMDD_HHMMSS_video_mp3/` - 개별 영상 MP3
- `YYYYMMDD_HHMMSS_channel/` - 채널 전체 영상
- `YYYYMMDD_HHMMSS_channel_mp3/` - 채널 전체 MP3

## API 엔드포인트

### POST /api/download/video
개별 영상을 MP4로 다운로드
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### POST /api/download/video-mp3
개별 영상을 MP3로 다운로드
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### POST /api/download/channel
채널 전체를 MP4로 다운로드
```json
{
  "url": "https://www.youtube.com/@CHANNEL_NAME/videos"
}
```

### POST /api/download/channel-mp3
채널 전체를 MP3로 다운로드
```json
{
  "url": "https://www.youtube.com/@CHANNEL_NAME/videos"
}
```

## 주의사항

- MP3 변환을 위해서는 FFmpeg가 시스템에 설치되어 있어야 합니다
- 채널 다운로드는 시간이 오래 걸릴 수 있습니다
- 저작권이 있는 콘텐츠는 개인적인 용도로만 사용하세요
- 서버가 0.0.0.0:8000으로 바인딩되므로 방화벽 설정을 확인하세요

## 기술 스택

- **FastAPI**: 웹 프레임워크
- **yt-dlp**: YouTube 다운로드 라이브러리
- **Uvicorn**: ASGI 서버
- **FFmpeg**: 오디오/비디오 처리
