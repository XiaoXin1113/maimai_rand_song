import httpx
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


DIVING_FISH_API_BASE = "https://www.diving-fish.com/api/maimaidxprober"


@dataclass
class PlayerScore:
    song_id: int
    title: str
    level: str
    level_index: int
    achievement: float
    dx_score: int
    dx_score_max: int
    fc: Optional[str]
    fs: Optional[str]
    rate: Optional[str]
    type: str
    
    @property
    def dx_rating(self) -> float:
        if self.dx_score_max == 0:
            return 0.0
        return (self.dx_score / self.dx_score_max) * 100.0


@dataclass
class PlayerInfo:
    username: str
    nickname: str
    rating: int
    additional_rating: int
    plate: Optional[str]


class DivingFishClient:
    def __init__(self, developer_token: Optional[str] = None):
        self.developer_token = developer_token
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _get_headers(self, import_token: Optional[str] = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.developer_token:
            headers["Developer-Token"] = self.developer_token
        if import_token:
            headers["Import-Token"] = import_token
        return headers
    
    async def get_player_info(self, username: str, import_token: Optional[str] = None) -> Optional[PlayerInfo]:
        url = f"{DIVING_FISH_API_BASE}/query/player"
        params = {"username": username}
        
        try:
            response = await self.client.get(url, params=params, headers=self._get_headers(import_token))
            if response.status_code == 200:
                data = response.json()
                return PlayerInfo(
                    username=data.get("username", ""),
                    nickname=data.get("nickname", ""),
                    rating=data.get("rating", 0),
                    additional_rating=data.get("additional_rating", 0),
                    plate=data.get("plate")
                )
        except Exception:
            pass
        return None
    
    async def get_player_records(self, username: str, import_token: Optional[str] = None) -> Optional[dict]:
        if self.developer_token:
            url = f"{DIVING_FISH_API_BASE}/dev/player/records"
            params = {"username": username}
        elif import_token:
            url = f"{DIVING_FISH_API_BASE}/player/records"
            params = {}
        else:
            return None
        
        try:
            response = await self.client.get(url, params=params, headers=self._get_headers(import_token))
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None
    
    async def get_song_score(
        self, 
        username: str, 
        song_id: int,
        level_index: int = 3,
        import_token: Optional[str] = None
    ) -> Optional[PlayerScore]:
        records = await self.get_player_records(username, import_token)
        if not records:
            return None
        
        records_list = records.get("records", {}).get("records", [])
        
        for record in records_list:
            if record.get("song_id") == song_id:
                level_records = record.get("levels", [])
                if level_index < len(level_records):
                    level_data = level_records[level_index]
                    return PlayerScore(
                        song_id=song_id,
                        title=record.get("title", ""),
                        level=level_data.get("level", ""),
                        level_index=level_index,
                        achievement=level_data.get("achievement", 0.0),
                        dx_score=level_data.get("dxScore", 0),
                        dx_score_max=level_data.get("dxScoreMax", 0),
                        fc=level_data.get("fc"),
                        fs=level_data.get("fs"),
                        rate=level_data.get("rate"),
                        type=record.get("type", "DX")
                    )
        return None
    
    async def get_song_score_by_name(
        self,
        username: str,
        song_title: str,
        difficulty: str = "master",
        song_type: str = "DX",
        import_token: Optional[str] = None
    ) -> Optional[PlayerScore]:
        records = await self.get_player_records(username, import_token)
        if not records:
            return None
        
        records_list = records.get("records", {}).get("records", [])
        
        difficulty_map = {
            "basic": 0,
            "advanced": 1,
            "expert": 2,
            "master": 3,
            "remaster": 4
        }
        level_index = difficulty_map.get(difficulty.lower(), 3)
        
        for record in records_list:
            if record.get("title") == song_title and record.get("type") == song_type:
                level_records = record.get("levels", [])
                if level_index < len(level_records):
                    level_data = level_records[level_index]
                    return PlayerScore(
                        song_id=record.get("song_id", 0),
                        title=song_title,
                        level=level_data.get("level", ""),
                        level_index=level_index,
                        achievement=level_data.get("achievement", 0.0),
                        dx_score=level_data.get("dxScore", 0),
                        dx_score_max=level_data.get("dxScoreMax", 0),
                        fc=level_data.get("fc"),
                        fs=level_data.get("fs"),
                        rate=level_data.get("rate"),
                        type=song_type
                    )
        return None
    
    async def close(self):
        await self.client.aclose()


diving_fish_client: Optional[DivingFishClient] = None


def init_diving_fish_client(developer_token: Optional[str] = None):
    global diving_fish_client
    diving_fish_client = DivingFishClient(developer_token)


def get_diving_fish_client() -> Optional[DivingFishClient]:
    return diving_fish_client
