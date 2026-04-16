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
    return FileResponse(Path(__file__).parent / "frontend" / "index.html")

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

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "frontend" / "static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
