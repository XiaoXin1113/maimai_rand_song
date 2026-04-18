import json
import random
from pathlib import Path
from typing import Optional
from datetime import datetime
from .models import Song, SelectionCriteria, SelectionResult, Difficulty, SongType, Chart

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "songs_database.json"


class SongManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, data_path: str = None):
        if data_path:
            self.data_path = Path(data_path)
        else:
            self.data_path = DATABASE_PATH
        self.songs: list[Song] = []
        self.last_loaded: Optional[datetime] = None
        self.load_songs()
    
    def load_songs(self) -> None:
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "songs" in data:
                    self.songs = [Song(**song) for song in data["songs"]]
                else:
                    self.songs = [Song(**song) for song in data]
            self.last_loaded = datetime.now()
        else:
            self.songs = []
    
    def reload_songs(self) -> None:
        self.load_songs()
    
    def save_songs(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump([song.model_dump() for song in self.songs], f, ensure_ascii=False, indent=2)
    
    def add_song(self, song: Song) -> None:
        if not any(s.id == song.id for s in self.songs):
            self.songs.append(song)
            self.save_songs()
    
    def get_song_by_id(self, song_id: int) -> Optional[Song]:
        for song in self.songs:
            if song.id == song_id:
                return song
        return None
    
    def get_song_by_title(self, title: str) -> Optional[Song]:
        for song in self.songs:
            if song.title == title:
                return song
            if title in song.alias:
                return song
        return None
    
    def get_all_songs(self) -> list[Song]:
        return self.songs
    
    def get_songs_by_genre(self, genre: str) -> list[Song]:
        return [s for s in self.songs if s.genre == genre]
    
    def get_songs_by_type(self, song_type: SongType) -> list[Song]:
        return [s for s in self.songs if s.type == song_type]
    
    def get_all_genres(self) -> list[str]:
        genres = set()
        for song in self.songs:
            if song.genre:
                genres.add(song.genre)
        return sorted(list(genres))
    
    def get_all_versions(self) -> list[str]:
        versions = set()
        for song in self.songs:
            if song.version:
                versions.add(song.version)
            for chart in song.charts:
                if chart.version:
                    versions.add(chart.version)
        return sorted(list(versions))


class SongSelector:
    def __init__(self, song_manager: SongManager):
        self.song_manager = song_manager
    
    def get_chart_level(self, song: Song, difficulty: Difficulty, song_type: SongType = None) -> Optional[float]:
        for chart in song.charts:
            if chart.difficulty == difficulty:
                if song_type is None or chart.type == song_type:
                    if chart.internal_level:
                        return chart.internal_level
                    try:
                        level_str = chart.level.replace("+", ".7")
                        return float(level_str)
                    except ValueError:
                        return None
        return None
    
    def filter_songs(self, criteria: SelectionCriteria) -> list[Song]:
        filtered = self.song_manager.get_all_songs()
        
        if criteria.song_type:
            filtered = [
                s for s in filtered 
                if any(chart.type == criteria.song_type for chart in s.charts)
            ]
        
        if criteria.genre:
            filtered = [s for s in filtered if s.genre == criteria.genre]
        
        if criteria.version:
            filtered = [
                s for s in filtered
                if s.version == criteria.version or any(c.version == criteria.version for c in s.charts)
            ]
        
        if criteria.difficulty:
            target_type = criteria.song_type if criteria.song_type else None
            
            if criteria.min_level is not None:
                filtered = [
                    s for s in filtered
                    if self.get_chart_level(s, criteria.difficulty, target_type) is not None
                    and self.get_chart_level(s, criteria.difficulty, target_type) >= criteria.min_level
                ]
            
            if criteria.max_level is not None:
                filtered = [
                    s for s in filtered
                    if self.get_chart_level(s, criteria.difficulty, target_type) is not None
                    and self.get_chart_level(s, criteria.difficulty, target_type) <= criteria.max_level
                ]
        
        return filtered
    
    def select_random(self, criteria: SelectionCriteria) -> SelectionResult:
        filtered = self.filter_songs(criteria)
        count = min(criteria.count, len(filtered))
        selected = random.sample(filtered, count) if filtered else []
        
        return SelectionResult(
            songs=selected,
            criteria=criteria,
            total_available=len(filtered)
        )


song_manager = SongManager()
song_selector = SongSelector(song_manager)
