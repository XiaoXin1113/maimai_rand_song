from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional
import sys
import json
import asyncio
import secrets
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType, Song
from core.group_blacklist import group_blacklist, BlacklistEntry

app = FastAPI(
    title="maimai随机选歌工具",
    description="Web API for maimai random song selector",
    version="Alpha-0.0.2"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

song_manager = SongManager()
song_selector = SongSelector(song_manager)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "songs_database.json"
AUTH_CONFIG_PATH = PROJECT_ROOT / "config" / "auth.json"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("maimai2024".encode()).hexdigest()
SESSION_EXPIRE_HOURS = 24

active_sessions = {}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_auth_config():
    if AUTH_CONFIG_PATH.exists():
        with open(AUTH_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_auth_config(config: dict):
    AUTH_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTH_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_admin_credentials():
    config = load_auth_config()
    username = config.get("admin_username", ADMIN_USERNAME)
    password_hash = config.get("admin_password_hash", ADMIN_PASSWORD_HASH)
    return username, password_hash

def create_session(username: str) -> str:
    session_token = secrets.token_urlsafe(32)
    active_sessions[session_token] = {
        "username": username,
        "expires": datetime.now() + timedelta(hours=SESSION_EXPIRE_HOURS)
    }
    return session_token

def validate_session(session_token: str) -> bool:
    if session_token not in active_sessions:
        return False
    session = active_sessions[session_token]
    if datetime.now() > session["expires"]:
        del active_sessions[session_token]
        return False
    return True

def get_session_from_request(request: Request) -> Optional[str]:
    session_token = request.cookies.get("session_token")
    if session_token and validate_session(session_token):
        return session_token
    return None

async def require_auth(request: Request):
    session_token = get_session_from_request(request)
    if not session_token:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")
    return session_token

class SelectionRequest(BaseModel):
    min_level: Optional[float] = None
    max_level: Optional[float] = None
    difficulty: Optional[str] = None
    song_type: Optional[str] = None
    genre: Optional[str] = None
    count: int = 1

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@app.get("/")
async def root():
    return FileResponse(Path(__file__).parent.parent / "frontend" / "index.html")

@app.get("/admin")
async def admin(request: Request):
    session_token = get_session_from_request(request)
    if not session_token:
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(Path(__file__).parent.parent / "frontend" / "admin.html")

@app.get("/login")
async def login_page():
    return FileResponse(Path(__file__).parent.parent / "frontend" / "login.html")

@app.post("/api/login")
async def login(request: LoginRequest, response: Response):
    username, password_hash = get_admin_credentials()
    
    if request.username != username or hash_password(request.password) != password_hash:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    session_token = create_session(username)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=SESSION_EXPIRE_HOURS * 3600,
        samesite="lax"
    )
    
    return {"message": "登录成功", "username": username}

@app.post("/api/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token and session_token in active_sessions:
        del active_sessions[session_token]
    
    response.delete_cookie("session_token")
    return {"message": "已退出登录"}

@app.get("/api/check-auth")
async def check_auth(request: Request):
    session_token = get_session_from_request(request)
    if session_token:
        return {"authenticated": True, "username": active_sessions[session_token]["username"]}
    return {"authenticated": False}

@app.post("/api/change-password")
async def change_password(request: ChangePasswordRequest, req: Request, session_token: str = Depends(require_auth)):
    username, old_password_hash = get_admin_credentials()
    
    if hash_password(request.old_password) != old_password_hash:
        raise HTTPException(status_code=400, detail="原密码错误")
    
    config = load_auth_config()
    config["admin_username"] = username
    config["admin_password_hash"] = hash_password(request.new_password)
    save_auth_config(config)
    
    return {"message": "密码修改成功"}

import socket

def check_bot_status():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 8080))
        sock.close()
        return result == 0
    except:
        return False

@app.get("/api/bot-status")
async def get_bot_status():
    is_online = check_bot_status()
    return {"online": is_online}

@app.get("/api/version")
async def get_version():
    return {"version": "Alpha-0.0.2"}

@app.get("/api/songs")
async def get_songs():
    return {"songs": [song.model_dump() for song in song_manager.get_all_songs()]}

@app.post("/api/select")
async def select_song(request: SelectionRequest):
    criteria = SelectionCriteria(
        min_level=request.min_level,
        max_level=request.max_level,
        difficulty=Difficulty(request.difficulty) if request.difficulty else None,
        song_type=SongType(request.song_type) if request.song_type else None,
        genre=request.genre,
        count=request.count
    )
    
    result = song_selector.select_random(criteria)
    return result.model_dump()

@app.get("/api/genres")
async def get_genres():
    genres = set()
    for song in song_manager.get_all_songs():
        if song.genre:
            genres.add(song.genre)
    return {"genres": list(genres)}

@app.get("/api/stats")
async def get_stats():
    songs = song_manager.get_all_songs()
    total_songs = len(songs)
    total_charts = sum(len(song.charts) for song in songs)
    return {"total_songs": total_songs, "total_charts": total_charts}

@app.post("/api/songs")
async def add_song(song: Song):
    song_manager.add_song(song)
    return {"message": "Song added successfully", "song": song.model_dump()}

class BlacklistAddRequest(BaseModel):
    group_id: int
    group_name: Optional[str] = None
    reason: Optional[str] = None

@app.get("/api/blacklist")
async def get_blacklist(session_token: str = Depends(require_auth)):
    return {"blacklist": [entry.model_dump() for entry in group_blacklist.get_all()]}

@app.post("/api/blacklist")
async def add_to_blacklist(request: BlacklistAddRequest, session_token: str = Depends(require_auth)):
    if group_blacklist.is_blocked(request.group_id):
        raise HTTPException(status_code=400, detail="该群聊已在黑名单中")
    entry = group_blacklist.add_group(
        group_id=request.group_id,
        group_name=request.group_name,
        reason=request.reason
    )
    return {"message": "已添加到黑名单", "entry": entry.model_dump()}

@app.delete("/api/blacklist/{group_id}")
async def remove_from_blacklist(group_id: int, session_token: str = Depends(require_auth)):
    if not group_blacklist.remove_group(group_id):
        raise HTTPException(status_code=404, detail="该群聊不在黑名单中")
    return {"message": "已从黑名单移除", "group_id": group_id}

@app.get("/api/blacklist/{group_id}")
async def check_blacklist_status(group_id: int):
    entry = group_blacklist.get_entry(group_id)
    if entry:
        return {"blocked": True, "entry": entry.model_dump()}
    return {"blocked": False}

@app.get("/api/database/stats")
async def get_database_stats(session_token: str = Depends(require_auth)):
    if not DATABASE_PATH.exists():
        return {
            "total_songs": 0,
            "total_charts": 0,
            "last_updated": "未找到数据库"
        }
    
    try:
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_songs = data.get("total_songs", len(data.get("songs", [])))
        total_charts = data.get("total_charts", 0)
        last_updated = data.get("last_updated", "未知")
        
        if not total_charts:
            songs = data.get("songs", [])
            total_charts = sum(len(song.get("charts", [])) for song in songs)
        
        return {
            "total_songs": total_songs,
            "total_charts": total_charts,
            "last_updated": last_updated
        }
    except Exception as e:
        return {
            "total_songs": 0,
            "total_charts": 0,
            "last_updated": f"读取错误: {str(e)}"
        }

@app.post("/api/database/update")
async def update_database(session_token: str = Depends(require_auth)):
    try:
        from scripts.update_database import update_database as do_update
        success = await do_update(force_download=True)
        
        if not success:
            raise HTTPException(status_code=500, detail="数据库更新失败")
        
        song_manager.load_songs()
        
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total_songs = data.get("total_songs", len(data.get("songs", [])))
        total_charts = data.get("total_charts", 0)
        last_updated = data.get("last_updated", datetime.now().isoformat())
        
        return {
            "success": True,
            "message": "数据库更新成功",
            "total_songs": total_songs,
            "total_charts": total_charts,
            "last_updated": last_updated
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库更新失败: {str(e)}")

app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "frontend" / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
