from .models import Song, Difficulty, SongType, SelectionCriteria, SelectionResult, Chart, NoteCounts, Regions, DatabaseMetadata
from .song_manager import SongManager, SongSelector, song_manager, song_selector
from .group_blacklist import GroupBlacklist, BlacklistEntry, group_blacklist
from .diving_fish import DivingFishClient, PlayerScore, PlayerInfo, init_diving_fish_client, get_diving_fish_client

def parse_level_input(level_str: str) -> tuple:
    """
    Parse level input string and return (min_level, max_level) tuple.
    
    Rules:
    - Integer input (e.g., 14): Matches 14.0 ~ 14.5 (broad level)
    - Plus input (e.g., 14+): Matches 14.6 ~ 14.9
    - Decimal input (e.g., 14.0): Matches exact level ± 0.05
    
    Returns:
        tuple: (min_level, max_level) or (None, None) if invalid
    """
    if not level_str:
        return None, None
        
    level_str = level_str.strip()
    has_plus = "+" in level_str
    level_str_clean = level_str.replace("+", "")
    has_decimal = "." in level_str_clean
    
    try:
        level = float(level_str_clean)
    except ValueError:
        return None, None
        
    if has_plus:
        level_int = int(level)
        min_level = level_int + 0.6
        max_level = level_int + 0.9
    elif not has_decimal and level == int(level):
        level_int = int(level)
        min_level = level_int + 0.0
        max_level = level_int + 0.5
    else:
        min_level = level - 0.05
        max_level = level + 0.05
        
    return min_level, max_level

__all__ = [
    "Song",
    "Difficulty",
    "SongType",
    "SelectionCriteria",
    "SelectionResult",
    "Chart",
    "NoteCounts",
    "Regions",
    "DatabaseMetadata",
    "SongManager",
    "SongSelector",
    "song_manager",
    "song_selector",
    "GroupBlacklist",
    "BlacklistEntry",
    "group_blacklist",
    "parse_level_input",
    "DivingFishClient",
    "PlayerScore",
    "PlayerInfo",
    "init_diving_fish_client",
    "get_diving_fish_client",
]
