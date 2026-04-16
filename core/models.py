from pydantic import BaseModel
from typing import Optional
from enum import Enum

class Difficulty(str, Enum):
    EASY = "Easy"
    BASIC = "Basic"
    ADVANCED = "Advanced"
    EXPERT = "Expert"
    MASTER = "Master"
    RE_MASTER = "Re:Master"

class SongType(str, Enum):
    STANDARD = "标准"
    DX = "DX"

class Song(BaseModel):
    id: str
    title: str
    artist: str
    type: SongType = SongType.STANDARD
    difficulties: dict[Difficulty, float] = {}
    genre: Optional[str] = None
    version: Optional[str] = None
    bpm: Optional[int] = None

class SelectionCriteria(BaseModel):
    min_level: Optional[float] = None
    max_level: Optional[float] = None
    difficulty: Optional[Difficulty] = None
    song_type: Optional[SongType] = None
    genre: Optional[str] = None
    exclude_played: bool = False
    count: int = 1

class SelectionResult(BaseModel):
    songs: list[Song]
    criteria: SelectionCriteria
    total_available: int
