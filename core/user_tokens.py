import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime


USER_TOKENS_PATH = Path(__file__).parent.parent / "data" / "user_tokens.json"


@dataclass
class UserToken:
    qq_id: int
    diving_fish_username: str
    import_token: str
    created_at: str
    updated_at: str


class UserTokenManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, data_path: str = None):
        if data_path:
            self.data_path = Path(data_path)
        else:
            self.data_path = USER_TOKENS_PATH
        self.tokens: dict[int, UserToken] = {}
        self.load_tokens()
    
    def load_tokens(self) -> None:
        if self.data_path.exists():
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tokens = {
                    int(k): UserToken(**v) for k, v in data.items()
                }
    
    def save_tokens(self) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(
                {str(k): asdict(v) for k, v in self.tokens.items()},
                f, ensure_ascii=False, indent=2
            )
    
    def set_token(self, qq_id: int, username: str, import_token: str) -> None:
        now = datetime.now().isoformat()
        if qq_id in self.tokens:
            self.tokens[qq_id].diving_fish_username = username
            self.tokens[qq_id].import_token = import_token
            self.tokens[qq_id].updated_at = now
        else:
            self.tokens[qq_id] = UserToken(
                qq_id=qq_id,
                diving_fish_username=username,
                import_token=import_token,
                created_at=now,
                updated_at=now
            )
        self.save_tokens()
    
    def get_token(self, qq_id: int) -> Optional[UserToken]:
        return self.tokens.get(qq_id)
    
    def remove_token(self, qq_id: int) -> bool:
        if qq_id in self.tokens:
            del self.tokens[qq_id]
            self.save_tokens()
            return True
        return False
    
    def has_token(self, qq_id: int) -> bool:
        return qq_id in self.tokens


user_token_manager = UserTokenManager()
