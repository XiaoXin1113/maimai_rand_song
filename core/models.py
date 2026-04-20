from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class Difficulty(str, Enum):
    EASY = "easy"
    BASIC = "basic"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"
    RE_MASTER = "remaster"
    UTAGE = "utage"


class SongType(str, Enum):
    STANDARD = "std"
    DX = "dx"
    UTAGE = "utage"


class Genre(str, Enum):
    POPS_ANIME = "POPS&ANIME"
    NICONICO_VOCALOID = "niconico&VOCALOID"
    TOUHOU = "TOUHOU"
    GAME_VARIETY = "GAME&VARIETY"
    MAIMAI = "maimai"
    ONGEKI_CHUNITHM = "ONGEKI&CHUNITHM"
    UTAGE = "UTAGE"


class NoteCounts(BaseModel):
    tap: int = 0
    hold: int = 0
    slide: int = 0
    touch: int = 0
    break_note: int = Field(default=0, alias="break")
    total: int = 0

    class Config:
        populate_by_name = True


class Regions(BaseModel):
    jp: bool = True
    intl: bool = True
    cn: bool = True
    usa: bool = False


class Chart(BaseModel):
    type: SongType
    difficulty: Difficulty
    level: str
    internal_level: Optional[float] = None
    note_designer: Optional[str] = None
    note_counts: Optional[NoteCounts] = None
    regions: Optional[Regions] = None
    version: Optional[str] = None
    release_date: Optional[str] = None
    utage_kanji: Optional[str] = None
    utage_comment: Optional[str] = None
    is_buddy: Optional[bool] = None


class Song(BaseModel):
    id: int
    title: str
    artist: str
    bpm: int
    genre: Optional[str] = None
    type: SongType = SongType.STANDARD
    image_url: Optional[str] = None
    charts: list[Chart] = []
    alias: list[str] = []
    tags: dict[str, list[int]] = {}
    regions: Optional[Regions] = None
    version: Optional[str] = None
    release_date: Optional[str] = None
    is_new: bool = False
    is_locked: bool = False


class SelectionCriteria(BaseModel):
    min_level: Optional[float] = None
    max_level: Optional[float] = None
    difficulty: Optional[Difficulty] = None
    song_type: Optional[SongType] = None
    genre: Optional[str] = None
    version: Optional[str] = None
    exclude_played: bool = False
    count: int = 1
    utage_only: bool = False


class SelectionResult(BaseModel):
    songs: list[Song]
    criteria: SelectionCriteria
    total_available: int


class DatabaseMetadata(BaseModel):
    last_updated: str
    total_songs: int
    total_charts: int
    source_version: dict[str, str] = {}
