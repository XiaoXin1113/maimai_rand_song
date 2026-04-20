import json
import random
from pathlib import Path
from typing import Optional
from datetime import datetime
from .models import Song, SelectionCriteria, SelectionResult, Difficulty, SongType, Chart

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "songs_database.json"


class SongManager:
    """歌曲管理器
    
    负责加载、保存和管理歌曲数据库，提供歌曲查询和操作功能。
    采用单例模式确保全局只有一个实例。
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """创建单例实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, data_path: str = None):
        """初始化歌曲管理器
        
        Args:
            data_path: 可选的数据库路径，默认使用项目默认路径
        """
        if data_path:
            self.data_path = Path(data_path)
        else:
            self.data_path = DATABASE_PATH
        self.songs: list[Song] = []
        self.last_loaded: Optional[datetime] = None
        self.load_songs()
    
    def load_songs(self) -> None:
        """从数据库文件加载歌曲数据"""
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
        """重新加载歌曲数据"""
        self.load_songs()
    
    def save_songs(self) -> None:
        """保存歌曲数据到数据库文件"""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump([song.model_dump() for song in self.songs], f, ensure_ascii=False, indent=2)
    
    def add_song(self, song: Song) -> None:
        """添加新歌曲到数据库
        
        Args:
            song: 要添加的歌曲对象
        """
        if not any(s.id == song.id for s in self.songs):
            self.songs.append(song)
            self.save_songs()
    
    def get_song_by_id(self, song_id: int) -> Optional[Song]:
        """根据歌曲ID获取歌曲
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            找到的歌曲对象，未找到则返回None
        """
        for song in self.songs:
            if song.id == song_id:
                return song
        return None
    
    def get_song_by_title(self, title: str) -> Optional[Song]:
        """根据歌曲标题或别名获取歌曲
        
        Args:
            title: 歌曲标题或别名
            
        Returns:
            找到的歌曲对象，未找到则返回None
        """
        for song in self.songs:
            if song.title == title:
                return song
            if title in song.alias:
                return song
        return None
    
    def get_all_songs(self) -> list[Song]:
        """获取所有歌曲
        
        Returns:
            歌曲列表
        """
        return self.songs
    
    def get_songs_by_genre(self, genre: str) -> list[Song]:
        """根据流派获取歌曲
        
        Args:
            genre: 歌曲流派
            
        Returns:
            符合条件的歌曲列表
        """
        return [s for s in self.songs if s.genre == genre]
    
    def get_songs_by_type(self, song_type: SongType) -> list[Song]:
        """根据歌曲类型获取歌曲
        
        Args:
            song_type: 歌曲类型（STANDARD、DX、UTAGE）
            
        Returns:
            符合条件的歌曲列表
        """
        return [s for s in self.songs if s.type == song_type]
    
    def get_all_genres(self) -> list[str]:
        """获取所有歌曲流派
        
        Returns:
            流派列表
        """
        genres = set()
        for song in self.songs:
            if song.genre:
                genres.add(song.genre)
        return sorted(list(genres))
    
    def get_all_versions(self) -> list[str]:
        """获取所有歌曲版本
        
        Returns:
            版本列表
        """
        versions = set()
        for song in self.songs:
            if song.version:
                versions.add(song.version)
            for chart in song.charts:
                if chart.version:
                    versions.add(chart.version)
        return sorted(list(versions))


class SongSelector:
    """歌曲选择器
    
    负责根据选择条件过滤和随机选择歌曲。
    """
    def __init__(self, song_manager: SongManager):
        """初始化歌曲选择器
        
        Args:
            song_manager: 歌曲管理器实例
        """
        self.song_manager = song_manager
    
    def get_chart_level(self, song: Song, difficulty: Difficulty, song_type: SongType = None) -> Optional[float]:
        """获取指定难度和类型的谱面等级
        
        Args:
            song: 歌曲对象
            difficulty: 难度级别
            song_type: 歌曲类型（可选）
            
        Returns:
            谱面等级，无法获取则返回None
        """
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
        """根据选择条件过滤歌曲
        
        Args:
            criteria: 选择条件
            
        Returns:
            符合条件的歌曲列表
        """
        filtered = self.song_manager.get_all_songs()
        
        # 按歌曲类型过滤
        if criteria.song_type:
            filtered = [
                s for s in filtered 
                if any(chart.type == criteria.song_type for chart in s.charts)
            ]
        
        # 按宴会场过滤
        if criteria.utage_only:
            # 只选择宴会场歌曲（类型为UTAGE或谱面类型为UTAGE）
            filtered = [
                s for s in filtered 
                if s.type == SongType.UTAGE or any(chart.type == SongType.UTAGE for chart in s.charts)
            ]
        else:
            # 只选择非宴会场歌曲（不是宴会场歌曲）
            filtered = [
                s for s in filtered 
                if not (s.type == SongType.UTAGE or any(chart.type == SongType.UTAGE for chart in s.charts))
            ]
        
        # 按流派过滤
        if criteria.genre:
            filtered = [s for s in filtered if s.genre == criteria.genre]
        
        # 按版本过滤
        if criteria.version:
            filtered = [
                s for s in filtered
                if s.version == criteria.version or any(c.version == criteria.version for c in s.charts)
            ]
        
        # 按等级范围过滤
        if criteria.min_level is not None or criteria.max_level is not None:
            target_difficulty = criteria.difficulty
            target_type = criteria.song_type
            
            def song_matches_level(song: Song) -> bool:
                """检查歌曲是否符合等级要求"""
                for chart in song.charts:
                    if target_difficulty and chart.difficulty != target_difficulty:
                        continue
                    if target_type and chart.type != target_type:
                        continue
                    
                    level = chart.internal_level
                    if level is None:
                        try:
                            level_str = chart.level.replace("+", ".7")
                            level = float(level_str)
                        except ValueError:
                            continue
                    
                    if level is None:
                        continue
                    
                    if criteria.min_level is not None and level < criteria.min_level:
                        continue
                    if criteria.max_level is not None and level > criteria.max_level:
                        continue
                    
                    return True
                return False
            
            filtered = [s for s in filtered if song_matches_level(s)]
        
        return filtered
    
    def select_random(self, criteria: SelectionCriteria) -> SelectionResult:
        """随机选择歌曲
        
        Args:
            criteria: 选择条件
            
        Returns:
            选择结果，包含选中的歌曲和相关信息
        """
        filtered = self.filter_songs(criteria)
        selected = random.choices(filtered, k=criteria.count) if filtered else []
        
        return SelectionResult(
            songs=selected,
            criteria=criteria,
            total_available=len(filtered)
        )


# 全局实例
song_manager = SongManager()
song_selector = SongSelector(song_manager)
