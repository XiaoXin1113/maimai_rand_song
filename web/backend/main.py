from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType, Song
from core.group_blacklist import group_blacklist, BlacklistEntry

app = FastAPI(
    title="maimai随机选歌工具",
    description="Web API for maimai random song selector",
    version="Alpha-0.0.1"
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

class SelectionRequest(BaseModel):
    min_level: Optional[float] = None
    max_level: Optional[float] = None
    difficulty: Optional[str] = None
    song_type: Optional[str] = None
    genre: Optional[str] = None
    count: int = 1

@app.get("/")
async def root():
    return FileResponse(Path(__file__).parent.parent / "frontend" / "index.html")

@app.get("/admin")
async def admin():
    return FileResponse(Path(__file__).parent.parent / "frontend" / "admin.html")

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
    return {"version": "Alpha-0.0.1"}

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

@app.post("/api/songs")
async def add_song(song: Song):
    song_manager.add_song(song)
    return {"message": "Song added successfully", "song": song.model_dump()}

class BlacklistAddRequest(BaseModel):
    group_id: int
    group_name: Optional[str] = None
    reason: Optional[str] = None

@app.get("/api/blacklist")
async def get_blacklist():
    return {"blacklist": [entry.model_dump() for entry in group_blacklist.get_all()]}

@app.post("/api/blacklist")
async def add_to_blacklist(request: BlacklistAddRequest):
    if group_blacklist.is_blocked(request.group_id):
        raise HTTPException(status_code=400, detail="该群聊已在黑名单中")
    entry = group_blacklist.add_group(
        group_id=request.group_id,
        group_name=request.group_name,
        reason=request.reason
    )
    return {"message": "已添加到黑名单", "entry": entry.model_dump()}

@app.delete("/api/blacklist/{group_id}")
async def remove_from_blacklist(group_id: int):
    if not group_blacklist.remove_group(group_id):
        raise HTTPException(status_code=404, detail="该群聊不在黑名单中")
    return {"message": "已从黑名单移除", "group_id": group_id}

@app.get("/api/blacklist/{group_id}")
async def check_blacklist_status(group_id: int):
    entry = group_blacklist.get_entry(group_id)
    if entry:
        return {"blocked": True, "entry": entry.model_dump()}
    return {"blocked": False}

app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "frontend" / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
