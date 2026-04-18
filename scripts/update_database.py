import json
import asyncio
import aiohttp
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Song, Chart, NoteCounts, Regions, Difficulty, SongType, DatabaseMetadata

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "songs_database.json"
METADATA_FILE = DATA_DIR / "database_metadata.json"

DATA_SOURCES = {
    "dxdata": "https://raw.githubusercontent.com/gekichumai/dxrating/main/packages/dxdata/dxdata.json",
    "songs_becods": "https://raw.githubusercontent.com/Becods/maimaiDX-CN-songs-alias-database/main/songs.json",
    "alias": "https://raw.githubusercontent.com/Becods/maimaiDX-CN-songs-alias-database/main/alias.json",
    "tags": "https://raw.githubusercontent.com/Becods/maimaiDX-CN-songs-alias-database/main/tags.json",
    "metadata": "https://raw.githubusercontent.com/Becods/maimaiDX-CN-songs-alias-database/main/metadata.json",
}

GENRE_MAP = {
    101: "POPS&ANIME",
    102: "niconico&VOCALOID",
    103: "TOUHOU",
    104: "GAME&VARIETY",
    105: "maimai",
    106: "ONGEKI&CHUNITHM",
    107: "UTAGE",
}

DIFFICULTY_MAP = {
    "basic": Difficulty.BASIC,
    "advanced": Difficulty.ADVANCED,
    "expert": Difficulty.EXPERT,
    "master": Difficulty.MASTER,
    "remaster": Difficulty.RE_MASTER,
    "utage": Difficulty.UTAGE,
}

TYPE_MAP = {
    "dx": SongType.DX,
    "std": SongType.STANDARD,
    "utage": SongType.UTAGE,
}


async def download_file(session: aiohttp.ClientSession, url: str, save_path: Path) -> Optional[dict]:
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                save_path.write_text(content, encoding='utf-8')
                logger.info(f"Downloaded: {save_path.name}")
                return json.loads(content)
            else:
                logger.error(f"Failed to download {url}: HTTP {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return None


async def fetch_all_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, url in DATA_SOURCES.items():
            save_path = DATA_DIR / f"{name}.json"
            tasks.append(download_file(session, url, save_path))
        
        results = await asyncio.gather(*tasks)
        
        for i, name in enumerate(DATA_SOURCES.keys()):
            if results[i]:
                data[name] = results[i]
    
    return data


def load_local_data() -> dict:
    data = {}
    for name in DATA_SOURCES.keys():
        file_path = DATA_DIR / f"{name}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data[name] = json.load(f)
    return data


def build_alias_map(alias_data: list) -> dict:
    alias_map = {}
    for item in alias_data:
        name = item.get("name", "")
        if name:
            alias_map[name] = item.get("alias", [])
    return alias_map


def build_tags_map(tags_data: list) -> dict:
    tags_map = {}
    for item in tags_data:
        name = item.get("name", "")
        song_type = item.get("type", 0)
        if name:
            key = f"{name}_{song_type}"
            tags_map[key] = item.get("tag", {})
    return tags_map


def parse_dxdata_sheets(sheets: list) -> list[Chart]:
    charts = []
    for sheet in sheets:
        sheet_type = sheet.get("type", "std")
        difficulty = sheet.get("difficulty", "basic")
        
        note_counts = None
        if "noteCounts" in sheet:
            nc = sheet["noteCounts"]
            note_counts = NoteCounts(
                tap=nc.get("tap") or 0,
                hold=nc.get("hold") or 0,
                slide=nc.get("slide") or 0,
                touch=nc.get("touch") or 0,
                break_note=nc.get("break") or 0,
                total=nc.get("total") or 0,
            )
        
        regions = None
        if "regions" in sheet:
            r = sheet["regions"]
            regions = Regions(
                jp=r.get("jp", False),
                intl=r.get("intl", False),
                cn=r.get("cn", False),
                usa=r.get("usa", False),
            )
        
        chart = Chart(
            type=TYPE_MAP.get(sheet_type, SongType.STANDARD),
            difficulty=DIFFICULTY_MAP.get(difficulty, Difficulty.BASIC),
            level=str(sheet.get("level", "")),
            internal_level=sheet.get("internalLevelValue"),
            note_designer=sheet.get("noteDesigner"),
            note_counts=note_counts,
            regions=regions,
            version=sheet.get("version"),
            release_date=sheet.get("releaseDate"),
        )
        charts.append(chart)
    
    return charts


def merge_data(data: dict) -> list[Song]:
    dxdata = data.get("dxdata", {}).get("songs", [])
    becods_songs = data.get("songs_becods", [])
    alias_data = data.get("alias", [])
    tags_data = data.get("tags", [])
    
    alias_map = build_alias_map(alias_data)
    tags_map = build_tags_map(tags_data)
    
    songs_dict = {}
    
    for song in dxdata:
        song_id = song.get("internalId") or song.get("songId")
        if song_id is None:
            continue
        if isinstance(song_id, str):
            try:
                song_id = int(song_id)
            except ValueError:
                continue
        
        title = song.get("title", "")
        
        charts = parse_dxdata_sheets(song.get("sheets", []))
        
        song_obj = Song(
            id=song_id,
            title=title,
            artist=song.get("artist", ""),
            bpm=song.get("bpm") or 0,
            genre=song.get("category"),
            image_url=song.get("imageName"),
            charts=charts,
            alias=alias_map.get(title, []),
            tags=tags_map.get(f"{title}_0", {}) or tags_map.get(f"{title}_1", {}),
            is_new=song.get("isNew", False),
            is_locked=song.get("isLocked", False),
        )
        
        key = f"{title}_{song.get('artist', '')}"
        songs_dict[key] = song_obj
    
    for song in becods_songs:
        song_id = song.get("id")
        title = song.get("name", "")
        
        if song_id is None:
            continue
        if song_id in [s.id for s in songs_dict.values()]:
            continue
        
        genre_id = song.get("genre")
        genre = GENRE_MAP.get(genre_id, "Unknown")
        
        song_type = TYPE_MAP.get(song.get("type", 0), SongType.STANDARD)
        
        charts = []
        for chart in song.get("charts", []):
            note_counts = None
            if "notes" in chart:
                notes = chart["notes"]
                note_counts = NoteCounts(
                    tap=notes[0] if len(notes) > 0 and notes[0] is not None else 0,
                    hold=notes[1] if len(notes) > 1 and notes[1] is not None else 0,
                    slide=notes[2] if len(notes) > 2 and notes[2] is not None else 0,
                    break_note=notes[3] if len(notes) > 3 and notes[3] is not None else 0,
                    touch=notes[4] if len(notes) > 4 and notes[4] is not None else 0,
                )
            
            regions = None
            if "regions" in song:
                r = song["regions"]
                regions = Regions(
                    jp=r.get("jp", True),
                    intl=r.get("intl", True),
                    cn=r.get("cn", True),
                )
            
            level = chart.get("level")
            if isinstance(level, float):
                if level >= 14.7:
                    level_str = "15"
                elif level >= 14.0:
                    level_str = "14+"
                elif level >= 13.7:
                    level_str = "14"
                elif level >= 13.0:
                    level_str = "13+"
                else:
                    level_str = str(int(level)) if level == int(level) else f"{int(level)}+"
            else:
                level_str = str(level)
            
            chart_obj = Chart(
                type=song_type,
                difficulty=Difficulty.MASTER,
                level=level_str,
                internal_level=chart.get("level") if isinstance(chart.get("level"), float) else None,
                note_designer=chart.get("charter"),
                note_counts=note_counts,
                regions=regions,
                release_date=song.get("date"),
            )
            charts.append(chart_obj)
        
        regions = None
        if "regions" in song:
            r = song["regions"]
            regions = Regions(
                jp=r.get("jp", True),
                intl=r.get("intl", True),
                cn=r.get("cn", True),
            )
        
        song_obj = Song(
            id=song_id,
            title=title,
            artist=song.get("artist", ""),
            bpm=song.get("bpm") or 0,
            genre=genre,
            type=song_type,
            image_url=song.get("dimg"),
            charts=charts,
            alias=alias_map.get(title, []),
            tags=tags_map.get(f"{title}_{song.get('type', 0)}", {}),
            regions=regions,
            release_date=song.get("date"),
        )
        
        key = f"{title}_{song.get('artist', '')}"
        if key not in songs_dict:
            songs_dict[key] = song_obj
    
    return list(songs_dict.values())


def save_database(songs: list[Song]) -> None:
    total_charts = sum(len(song.charts) for song in songs)
    
    metadata = DatabaseMetadata(
        last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_songs=len(songs),
        total_charts=total_charts,
        source_version={
            "dxdata": "latest",
            "becods": "latest",
        }
    )
    
    output_data = {
        "metadata": metadata.model_dump(),
        "songs": [song.model_dump() for song in songs],
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Database saved: {OUTPUT_FILE}")
    logger.info(f"Total songs: {len(songs)}, Total charts: {total_charts}")


async def update_database(force_download: bool = False) -> bool:
    try:
        if force_download:
            data = await fetch_all_data()
        else:
            data = load_local_data()
            if not data:
                data = await fetch_all_data()
        
        if not data:
            logger.error("No data available")
            return False
        
        songs = merge_data(data)
        save_database(songs)
        return True
    
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(update_database(force_download=True))
