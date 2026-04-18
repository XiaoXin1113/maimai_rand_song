# maimai_rand_song 配置文件

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    VERSION: str = "Alpha-0.0.2"
    APP_NAME: str = "maimai随机选歌工具"
    
    # QQ机器人配置
    BOT_SUPERUSERS: list[str] = []
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

settings = Settings()
