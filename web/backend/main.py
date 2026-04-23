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
import httpx
import socket
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType, Song
from core.group_blacklist import group_blacklist, BlacklistEntry

COVER_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "covers"
COVER_CACHE_DIR.mkdir(parents=True, exist_ok=True)

COVER_SOURCES = [
    "https://raw.githubusercontent.com/realtvop/maimai_music_metadata/main/covers",
]

async def fetch_cover(song_id: int) -> Optional[bytes]:
    cover_filename = f"{song_id:06d}.png"
    cache_path = COVER_CACHE_DIR / cover_filename
    
    if cache_path.exists():
        return cache_path.read_bytes()
    
    async with httpx.AsyncClient(timeout=10) as client:
        for source in COVER_SOURCES:
            try:
                url = f"{source}/{cover_filename}"
                response = await client.get(url)
                if response.status_code == 200:
                    cache_path.write_bytes(response.content)
                    return response.content
            except Exception:
                continue
    
    return None

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
    utage_only: bool = False

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

def check_bot_status():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 8080))
        sock.close()
        return result == 0
    except:
        return False

SERVICE_CONFIG_PATH = PROJECT_ROOT / "config" / "service_config.json"

def load_service_config():
    if SERVICE_CONFIG_PATH.exists():
        with open(SERVICE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"bot_enabled": True}

def save_service_config(config: dict):
    SERVICE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SERVICE_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def restart_service(service_name: str) -> bool:
    try:
        if service_name == "bot":
            cmd = 'screen -S bot -X quit; sleep 1; screen -dmS bot bash -c "cd ~/maimai_rand_song/bot && python3 main.py 2>&1 | tee /tmp/bot.log"'
            subprocess.Popen(cmd, shell=True)
            return True
        elif service_name == "web":
            restart_script = '''#!/bin/bash
# 等待3秒确保当前请求完成
sleep 3

# 关闭旧的web服务
screen -S web -X quit 2>/dev/null

# 等待1秒确保服务完全关闭
sleep 1

# 启动新的web服务
screen -dmS web bash -c "cd ~/maimai_rand_song && python3 -m web.backend.main 2>&1 | tee /tmp/web.log"
'''
            script_path = '/tmp/web_restart.sh'
            with open(script_path, 'w') as f:
                f.write(restart_script)
            import os
            os.chmod(script_path, 0o755)
            
            # 使用nohup在完全独立的进程中执行
            nohup_cmd = f'nohup bash {script_path} > /dev/null 2>&1 &'
            subprocess.Popen(nohup_cmd, shell=True)
            return True
        return False
    except Exception as e:
        print(f"Error restarting {service_name}: {e}")
        return False

@app.get("/api/bot-status")
async def get_bot_status():
    is_online = check_bot_status()
    return {"online": is_online}

class ServiceEnabledRequest(BaseModel):
    enabled: bool

@app.get("/api/service/enabled")
async def get_service_enabled(session_token: str = Depends(require_auth)):
    config = load_service_config()
    return {"bot_enabled": config.get("bot_enabled", True)}

@app.post("/api/service/enabled")
async def set_service_enabled(request: ServiceEnabledRequest, session_token: str = Depends(require_auth)):
    config = load_service_config()
    config["bot_enabled"] = request.enabled
    save_service_config(config)

    if not request.enabled:
        try:
            cmd = 'screen -S bot -X quit'
            subprocess.Popen(cmd, shell=True)
        except:
            pass
    else:
        restart_service("bot")

    return {"message": f"Bot服务已{'启用' if request.enabled else '禁用'}", "bot_enabled": request.enabled}

@app.post("/api/service/restart/{service_name}")
async def restart_service_endpoint(service_name: str, session_token: str = Depends(require_auth)):
    if service_name not in ["bot", "web"]:
        raise HTTPException(status_code=400, detail="无效的服务名称")

    success = restart_service(service_name)
    if success:
        return {"message": f"{service_name}服务重启成功"}
    raise HTTPException(status_code=500, detail=f"{service_name}服务重启失败")

@app.get("/api/version")
async def get_version():
    return {"version": "Alpha-0.0.2"}

@app.get("/api/cover/{song_id}")
async def get_cover(song_id: int):
    cover_data = await fetch_cover(song_id)
    if cover_data:
        return Response(content=cover_data, media_type="image/png")
    raise HTTPException(status_code=404, detail="Cover not found")

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
        count=request.count,
        utage_only=request.utage_only
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
        
        # 检查data是否为列表（直接保存的歌曲列表）
        if isinstance(data, list):
            total_songs = len(data)
            total_charts = sum(len(song.get("charts", [])) for song in data)
            last_updated = "未知"
        else:
            # 兼容旧格式
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
