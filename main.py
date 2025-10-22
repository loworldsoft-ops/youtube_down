from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
from datetime import datetime
from pathlib import Path
import os
import re

app = FastAPI(title="YouTube Downloader")

# 기본 다운로드 경로
BASE_DOWNLOAD_PATH = r"D:\ftp\minjung"

class VideoRequest(BaseModel):
    url: str

class ChannelRequest(BaseModel):
    url: str

def sanitize_filename(filename: str) -> str:
    """파일명에서 사용할 수 없는 문자 제거"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def create_download_folder(alias: str) -> Path:
    """날짜와 알리아스로 폴더 생성"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{date_str}_{alias}"
    folder_path = Path(BASE_DOWNLOAD_PATH) / folder_name
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path

@app.get("/")
async def root():
    """메인 웹 페이지 반환"""
    return FileResponse("static/index.html")

@app.post("/api/download/video")
async def download_video(request: VideoRequest):
    """영상 주소로 비디오 다운로드"""
    try:
        download_path = create_download_folder("video")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(download_path / '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            
        return JSONResponse({
            "status": "success",
            "message": f"비디오 다운로드 완료: {info.get('title', 'Unknown')}",
            "path": str(download_path),
            "filename": Path(filename).name
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")

@app.post("/api/download/video-mp3")
async def download_video_mp3(request: VideoRequest):
    """영상 주소로 MP3 다운로드"""
    try:
        download_path = create_download_folder("video_mp3")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(download_path / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            
        return JSONResponse({
            "status": "success",
            "message": f"MP3 다운로드 완료: {info.get('title', 'Unknown')}",
            "path": str(download_path),
            "filename": f"{sanitize_filename(info.get('title', 'audio'))}.mp3"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")

@app.post("/api/download/channel")
async def download_channel(request: ChannelRequest):
    """채널의 모든 비디오 다운로드"""
    try:
        download_path = create_download_folder("channel")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(download_path / '%(playlist_index)s_%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'ignoreerrors': True,  # 개별 비디오 오류 무시하고 계속 진행
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            video_count = len(info.get('entries', [])) if 'entries' in info else 1
            
        return JSONResponse({
            "status": "success",
            "message": f"채널 다운로드 완료: {video_count}개 비디오",
            "path": str(download_path),
            "video_count": video_count
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")

@app.post("/api/download/channel-mp3")
async def download_channel_mp3(request: ChannelRequest):
    """채널의 모든 비디오를 MP3로 다운로드"""
    try:
        download_path = create_download_folder("channel_mp3")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(download_path / '%(playlist_index)s_%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ignoreerrors': True,  # 개별 비디오 오류 무시하고 계속 진행
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            video_count = len(info.get('entries', [])) if 'entries' in info else 1
            
        return JSONResponse({
            "status": "success",
            "message": f"채널 MP3 다운로드 완료: {video_count}개 오디오",
            "path": str(download_path),
            "video_count": video_count
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 실패: {str(e)}")

@app.get("/api/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok", "message": "서버가 정상 작동 중입니다."}

# 정적 파일 제공
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0으로 바인딩하여 외부 접속 허용
    uvicorn.run(app, host="0.0.0.0", port=8000)
