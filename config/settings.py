# maimai_rand_song 配置文件

from pydantic_settings import BaseSettings
from typing import Optional
import json

class Settings(BaseSettings):
    VERSION: str = "Alpha-0.0.2"
    APP_NAME: str = "maimai随机选歌工具"
    
    # QQ机器人配置
    BOT_SUPERUSERS: list[str] = []
    SUPERUSER: str = ""
    BOT_HOST: str = "127.0.0.1"
    BOT_PORT: int = 8080
    
    # Web服务配置
    WEB_HOST: str = "127.0.0.1"
    WEB_PORT: int = 8000
    
    # 数据文件路径
    SONGS_DATA_PATH: str = "data/songs.json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.SUPERUSER:
            try:
                superusers_list = json.loads(self.SUPERUSER)
                if isinstance(superusers_list, list):
                    self.BOT_SUPERUSERS = superusers_list
                else:
                    self.BOT_SUPERUSERS = [str(self.SUPERUSER)]
            except json.JSONDecodeError:
                self.BOT_SUPERUSERS = [self.SUPERUSER]
        
        if self.BOT_SUPERUSERS == [""]:
            self.BOT_SUPERUSERS = []

settings = Settings()
