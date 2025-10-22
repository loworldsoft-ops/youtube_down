from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
from datetime import datetime
from pathlib import Path
import os
import re
import logging
import json
import asyncio
from typing import Set
import threading
import queue

app = FastAPI(title="YouTube Downloader")

# 기본 다운로드 경로
BASE_DOWNLOAD_PATH = r"D:\ftp\minjung"
LOG_PATH = Path("logs")

# WebSocket 연결 관리
active_connections: Set[WebSocket] = set()
# 메시지 큐
message_queue = queue.Queue()

# 로깅 설정
def setup_logger():
    """날짜별 로그 디렉토리 생성 및 로거 설정"""
    date_str = datetime.now().strftime("%Y%m%d")
    log_dir = LOG_PATH / date_str
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"download_{datetime.now().strftime('%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

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

async def broadcast_message(message: dict):
    """모든 WebSocket 연결에 메시지 브로드캐스트"""
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.add(connection)
    
    # 끊어진 연결 제거
    active_connections.difference_update(disconnected)

def create_progress_hook(download_id: str, alias: str):
    """yt-dlp 진행상태 훅 생성"""
    def progress_hook(d):
        try:
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                percent = (downloaded / total * 100) if total > 0 else 0
                
                message = {
                    'type': 'progress',
                    'download_id': download_id,
                    'alias': alias,
                    'status': 'downloading',
                    'percent': round(percent, 1),
                    'downloaded': downloaded,
                    'total': total,
                    'speed': speed if speed else 0,
                    'eta': eta if eta else 0,
                    'filename': d.get('filename', '')
                }
                
                # 큐에 메시지 추가
                message_queue.put(message)
                
            elif d['status'] == 'finished':
                message = {
                    'type': 'progress',
                    'download_id': download_id,
                    'alias': alias,
                    'status': 'finished',
                    'filename': d.get('filename', '')
                }
                
                message_queue.put(message)
                
        except Exception as e:
            logger.error(f"Progress hook error: {str(e)}")
    
    return progress_hook

# 백그라운드에서 메시지 큐 처리
async def process_message_queue():
    """메시지 큐를 처리하여 WebSocket으로 전송"""
    while True:
        try:
            if not message_queue.empty():
                message = message_queue.get_nowait()
                await broadcast_message(message)
            await asyncio.sleep(0.1)  # 100ms마다 체크
        except Exception as e:
            logger.error(f"Message queue processing error: {str(e)}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 백그라운드 작업 시작"""
    asyncio.create_task(process_message_queue())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결 엔드포인트"""
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/")
async def root():
    """메인 웹 페이지 반환"""
    return FileResponse("static/index.html")

@app.post("/api/download/video")
async def download_video(request: VideoRequest):
    """영상 주소로 비디오 다운로드"""
    download_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    try:
        logger.info(f"[{download_id}] Starting video download: {request.url}")
        download_path = create_download_folder("video")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(download_path / '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'progress_hooks': [create_progress_hook(download_id, 'video')],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
        
        logger.info(f"[{download_id}] Video download completed: {info.get('title', 'Unknown')}")
        
        await broadcast_message({
            'type': 'complete',
            'download_id': download_id,
            'alias': 'video',
            'status': 'success',
            'title': info.get('title', 'Unknown')
        })
            
        return JSONResponse({
            "status": "success",
            "message": f"비디오 다운로드 완료: {info.get('title', 'Unknown')}",
            "path": str(download_path),
            "filename": Path(filename).name,
            "download_id": download_id
        })
    except Exception as e:
        error_msg = f"다운로드 실패: {str(e)}"
        logger.error(f"[{download_id}] {error_msg}", exc_info=True)
        
        await broadcast_message({
            'type': 'error',
            'download_id': download_id,
            'alias': 'video',
            'error': str(e)
        })
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/download/video-mp3")
async def download_video_mp3(request: VideoRequest):
    """영상 주소로 MP3 다운로드"""
    download_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    try:
        logger.info(f"[{download_id}] Starting MP3 download: {request.url}")
        download_path = create_download_folder("video_mp3")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(download_path / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [create_progress_hook(download_id, 'video_mp3')],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
        
        logger.info(f"[{download_id}] MP3 download completed: {info.get('title', 'Unknown')}")
        
        await broadcast_message({
            'type': 'complete',
            'download_id': download_id,
            'alias': 'video_mp3',
            'status': 'success',
            'title': info.get('title', 'Unknown')
        })
            
        return JSONResponse({
            "status": "success",
            "message": f"MP3 다운로드 완료: {info.get('title', 'Unknown')}",
            "path": str(download_path),
            "filename": f"{sanitize_filename(info.get('title', 'audio'))}.mp3",
            "download_id": download_id
        })
    except Exception as e:
        error_msg = f"다운로드 실패: {str(e)}"
        logger.error(f"[{download_id}] {error_msg}", exc_info=True)
        
        await broadcast_message({
            'type': 'error',
            'download_id': download_id,
            'alias': 'video_mp3',
            'error': str(e)
        })
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/download/channel")
async def download_channel(request: ChannelRequest):
    """채널의 모든 비디오 다운로드"""
    download_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    try:
        logger.info(f"[{download_id}] Starting channel download: {request.url}")
        download_path = create_download_folder("channel")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': str(download_path / '%(playlist_index)s_%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'ignoreerrors': True,  # 개별 비디오 오류 무시하고 계속 진행
            'progress_hooks': [create_progress_hook(download_id, 'channel')],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            video_count = len(info.get('entries', [])) if 'entries' in info else 1
        
        logger.info(f"[{download_id}] Channel download completed: {video_count} videos")
        
        await broadcast_message({
            'type': 'complete',
            'download_id': download_id,
            'alias': 'channel',
            'status': 'success',
            'video_count': video_count
        })
            
        return JSONResponse({
            "status": "success",
            "message": f"채널 다운로드 완료: {video_count}개 비디오",
            "path": str(download_path),
            "video_count": video_count,
            "download_id": download_id
        })
    except Exception as e:
        error_msg = f"다운로드 실패: {str(e)}"
        logger.error(f"[{download_id}] {error_msg}", exc_info=True)
        
        await broadcast_message({
            'type': 'error',
            'download_id': download_id,
            'alias': 'channel',
            'error': str(e)
        })
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/download/channel-mp3")
async def download_channel_mp3(request: ChannelRequest):
    """채널의 모든 비디오를 MP3로 다운로드"""
    download_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    try:
        logger.info(f"[{download_id}] Starting channel MP3 download: {request.url}")
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
            'progress_hooks': [create_progress_hook(download_id, 'channel_mp3')],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            video_count = len(info.get('entries', [])) if 'entries' in info else 1
        
        logger.info(f"[{download_id}] Channel MP3 download completed: {video_count} audios")
        
        await broadcast_message({
            'type': 'complete',
            'download_id': download_id,
            'alias': 'channel_mp3',
            'status': 'success',
            'video_count': video_count
        })
            
        return JSONResponse({
            "status": "success",
            "message": f"채널 MP3 다운로드 완료: {video_count}개 오디오",
            "path": str(download_path),
            "video_count": video_count,
            "download_id": download_id
        })
    except Exception as e:
        error_msg = f"다운로드 실패: {str(e)}"
        logger.error(f"[{download_id}] {error_msg}", exc_info=True)
        
        await broadcast_message({
            'type': 'error',
            'download_id': download_id,
            'alias': 'channel_mp3',
            'error': str(e)
        })
        
        raise HTTPException(status_code=500, detail=error_msg)

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
