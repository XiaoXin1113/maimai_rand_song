import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

class BlacklistEntry(BaseModel):
    group_id: int
    group_name: Optional[str] = None
    reason: Optional[str] = None

class GroupBlacklist:
    def __init__(self, data_path: str = "data/blacklist.json"):
        self.data_path = Path(data_path)
        self._blacklist: dict[int, BlacklistEntry] = {}
        self._load()
    
    def _load(self):
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._blacklist = {
                        int(k): BlacklistEntry(**v) 
                        for k, v in data.get("blacklist", {}).items()
                    }
            except (json.JSONDecodeError, KeyError):
                self._blacklist = {}
        else:
            self._blacklist = {}
    
    def _save(self):
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "blacklist": {
                str(k): v.model_dump() 
                for k, v in self._blacklist.items()
            }
        }
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def is_blocked(self, group_id: int) -> bool:
        return group_id in self._blacklist
    
    def add_group(self, group_id: int, group_name: Optional[str] = None, 
                  reason: Optional[str] = None) -> BlacklistEntry:
        entry = BlacklistEntry(
            group_id=group_id,
            group_name=group_name,
            reason=reason
        )
        self._blacklist[group_id] = entry
        self._save()
        return entry
    
    def remove_group(self, group_id: int) -> bool:
        if group_id in self._blacklist:
            del self._blacklist[group_id]
            self._save()
            return True
        return False
    
    def get_all(self) -> list[BlacklistEntry]:
        return list(self._blacklist.values())
    
    def get_entry(self, group_id: int) -> Optional[BlacklistEntry]:
        return self._blacklist.get(group_id)

group_blacklist = GroupBlacklist()
