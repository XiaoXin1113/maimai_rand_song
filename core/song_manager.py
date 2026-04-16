import json
import random
from pathlib import Path
from typing import Optional
from .models import Song, SelectionCriteria, SelectionResult

class SongManager:
    def __init__(self, data_path: str = "data/songs.json"):
        self.data_path = Path(data_path)
        self.songs: list[Song] = []
        self.load_songs()
    
    def load_songs(self) -> None:
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.songs = [Song(**song) for song in data]
        else:
            self.songs = []
    
    def save_songs(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump([song.model_dump() for song in self.songs], f, ensure_ascii=False, indent=2)
    
    def add_song(self, song: Song) -> None:
        if not any(s.id == song.id for s in self.songs):
            self.songs.append(song)
            self.save_songs()
    
    def get_song_by_id(self, song_id: str) -> Optional[Song]:
        for song in self.songs:
            if song.id == song_id:
                return song
        return None
    
    def get_all_songs(self) -> list[Song]:
        return self.songs

class SongSelector:
    def __init__(self, song_manager: SongManager):
        self.song_manager = song_manager
    
    def filter_songs(self, criteria: SelectionCriteria) -> list[Song]:
        filtered = self.song_manager.get_all_songs()
        
        if criteria.song_type:
            filtered = [s for s in filtered if s.type == criteria.song_type]
        
        if criteria.genre:
            filtered = [s for s in filtered if s.genre == criteria.genre]
        
        if criteria.difficulty and criteria.min_level is not None:
            filtered = [
                s for s in filtered
                if s.difficulties.get(criteria.difficulty, 0) >= criteria.min_level
            ]
        
        if criteria.difficulty and criteria.max_level is not None:
            filtered = [
                s for s in filtered
                if s.difficulties.get(criteria.difficulty, 15) <= criteria.max_level
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
