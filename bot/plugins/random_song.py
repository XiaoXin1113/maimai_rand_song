import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nonebot import on_command, on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, Event, MessageSegment
from nonebot.params import CommandArg
from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType, parse_level_input
from core.group_blacklist import group_blacklist

COVER_BASE_URL = "http://127.0.0.1:8000/api/cover"

def get_cover_url(song_id: int) -> str:
    return f"{COVER_BASE_URL}/{song_id}"

song_manager = SongManager()
song_selector = SongSelector(song_manager)

DIFFICULTY_NAMES = {
    Difficulty.EASY: "Easy",
    Difficulty.BASIC: "Basic",
    Difficulty.ADVANCED: "Advanced",
    Difficulty.EXPERT: "Expert",
    Difficulty.MASTER: "Master",
    Difficulty.RE_MASTER: "Re:Master",
    Difficulty.UTAGE: "Utage",
}

TYPE_NAMES = {
    SongType.STANDARD: "std",
    SongType.DX: "DX",
    SongType.UTAGE: "Utage",
}

async def check_blacklist(event: Event) -> bool:
    if isinstance(event, GroupMessageEvent):
        return not group_blacklist.is_blocked(event.group_id)
    return True

random_song = on_command("random_song", aliases={"rs"}, priority=5, block=True, rule=check_blacklist)

@random_song.handle()
async def handle_random_song(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    
    criteria = SelectionCriteria(count=1)
    target_difficulty = Difficulty.MASTER
    target_type = None
    
    for part in parts:
        part_lower = part.lower()
        
        if part_lower in ["dx", "std"]:
            criteria.song_type = SongType.DX if part_lower == "dx" else SongType.STANDARD
            target_type = criteria.song_type
        elif part_lower in ["easy", "ez"]:
            target_difficulty = Difficulty.EASY
        elif part_lower in ["basic", "bs", "b"]:
            target_difficulty = Difficulty.BASIC
        elif part_lower in ["advanced", "adv", "a"]:
            target_difficulty = Difficulty.ADVANCED
        elif part_lower in ["expert", "exp", "e"]:
            target_difficulty = Difficulty.EXPERT
        elif part_lower in ["master", "mas", "m"]:
            target_difficulty = Difficulty.MASTER
        elif part_lower in ["remaster", "rem", "r"]:
            target_difficulty = Difficulty.RE_MASTER
        elif part_lower in ["utage", "u"]:
            target_difficulty = Difficulty.UTAGE
            criteria.song_type = SongType.UTAGE
            target_type = SongType.UTAGE
        else:
            min_lv, max_lv = parse_level_input(part)
            if min_lv is not None:
                criteria.min_level = min_lv
                criteria.max_level = max_lv
    
    criteria.difficulty = target_difficulty
    
    result = song_selector.select_random(criteria)
    
    if result.songs:
        song = result.songs[0]
        msg = f"Random Song Result\n\n"
        msg += f"Title: {song.title}\n"
        msg += f"Artist: {song.artist}\n"
        
        if song.genre:
            msg += f"Genre: {song.genre}\n"
        
        msg += f"BPM: {song.bpm}\n"
        
        matching_charts = []
        for chart in song.charts:
            if target_type and chart.type != target_type:
                continue
            if chart.difficulty == target_difficulty:
                matching_charts.append(chart)
        
        if matching_charts:
            chart = matching_charts[0]
            type_str = TYPE_NAMES.get(chart.type, chart.type.value)
            diff_str = DIFFICULTY_NAMES.get(chart.difficulty, chart.difficulty.value)
            level_display = chart.level
            if chart.internal_level:
                level_display += f" ({chart.internal_level:.1f})"
            
            msg += f"\n[{type_str}] {diff_str} {level_display}\n"
            
            if chart.note_designer:
                msg += f"Charter: {chart.note_designer}\n"
            
            if chart.note_counts:
                nc = chart.note_counts
                msg += f"Notes: Tap {nc.tap} / Hold {nc.hold} / Slide {nc.slide}"
                if nc.touch > 0:
                    msg += f" / Touch {nc.touch}"
                if nc.break_note > 0:
                    msg += f" / Break {nc.break_note}"
                msg += f" (Total {nc.total})\n"
        
        if song.alias and len(song.alias) > 0:
            aliases_str = ", ".join(song.alias[:3])
            if len(song.alias) > 3:
                aliases_str += "..."
            msg += f"\nAlias: {aliases_str}\n"
        
        msg += f"\nFound {result.total_available} matching songs"
        
        await random_song.send(msg)
        
        try:
            cover_url = get_cover_url(song.id)
            await random_song.send(MessageSegment.image(cover_url))
        except Exception:
            pass
    else:
        await random_song.finish("No matching songs found. Try adjusting your criteria.")

search_song = on_command("search", aliases={"find"}, priority=5, block=True, rule=check_blacklist)

@search_song.handle()
async def handle_search_song(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    keyword = args.extract_plain_text().strip()
    
    if not keyword:
        await search_song.finish("Please enter a song name or alias to search")
    
    all_songs = song_manager.get_all_songs()
    results = []
    
    for song in all_songs:
        if keyword.lower() in song.title.lower():
            results.append(song)
        elif any(keyword.lower() in alias.lower() for alias in song.alias):
            results.append(song)
    
    if not results:
        await search_song.finish(f"No songs found containing \"{keyword}\"")
    
    if len(results) == 1:
        song = results[0]
        msg = f"Search Result\n\n"
        msg += f"Title: {song.title}\n"
        msg += f"Artist: {song.artist}\n"
        
        if song.genre:
            msg += f"Genre: {song.genre}\n"
        
        msg += f"BPM: {song.bpm}\n"
        msg += f"Type: {TYPE_NAMES.get(song.type, song.type.value)}\n"
        
        msg += f"\nDifficulty List:\n"
        
        chart_groups = {}
        for chart in song.charts:
            key = chart.type.value
            if key not in chart_groups:
                chart_groups[key] = []
            chart_groups[key].append(chart)
        
        for chart_type in [SongType.STANDARD, SongType.DX, SongType.UTAGE]:
            if chart_type.value in chart_groups:
                type_str = TYPE_NAMES.get(chart_type, chart_type.value)
                msg += f"\n[{type_str}]\n"
                for chart in sorted(chart_groups[chart_type.value], key=lambda c: list(Difficulty).index(c.difficulty)):
                    diff_str = DIFFICULTY_NAMES.get(chart.difficulty, chart.difficulty.value)
                    level_display = chart.level
                    if chart.internal_level:
                        level_display += f"({chart.internal_level:.1f})"
                    msg += f"  {diff_str}: {level_display}\n"
        
        if song.alias and len(song.alias) > 0:
            msg += f"\nAlias: {', '.join(song.alias)}\n"
        
        await search_song.send(msg.strip())
        
        try:
            cover_url = get_cover_url(song.id)
            await search_song.send(MessageSegment.image(cover_url))
        except Exception:
            pass
    else:
        msg = f"Found {len(results)} related songs:\n\n"
        for i, song in enumerate(results[:10], 1):
            msg += f"{i}. {song.title} - {song.artist}\n"
        
        if len(results) > 10:
            msg += f"\n... and {len(results) - 10} more"
        
        await search_song.finish(msg.strip())

level_list = on_command("level", aliases={"lv"}, priority=5, block=True, rule=check_blacklist)

@level_list.handle()
async def handle_level_list(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    
    min_level = None
    max_level = None
    target_difficulty = Difficulty.MASTER
    level_display = None
    
    for part in parts:
        part_lower = part.lower()
        
        if part_lower in ["master", "mas", "m"]:
            target_difficulty = Difficulty.MASTER
        elif part_lower in ["remaster", "rem", "r"]:
            target_difficulty = Difficulty.RE_MASTER
        elif part_lower in ["expert", "exp", "e"]:
            target_difficulty = Difficulty.EXPERT
        else:
            min_lv, max_lv = parse_level_input(part)
            if min_lv is not None:
                min_level = min_lv
                max_level = max_lv
                level_display = part.replace(".7", "+")
    
    if min_level is None:
        await level_list.finish("Please specify a level, e.g.: level 14, level 14+, level 14.5")
    
    all_songs = song_manager.get_all_songs()
    results = []
    
    for song in all_songs:
        for chart in song.charts:
            if chart.difficulty == target_difficulty and chart.internal_level:
                if min_level <= chart.internal_level <= max_level:
                    results.append((song, chart))
    
    if not results:
        diff_str = DIFFICULTY_NAMES.get(target_difficulty, target_difficulty.value)
        await level_list.finish(f"No {diff_str} charts found with level {level_display}")
    
    results.sort(key=lambda x: x[0].title)
    
    diff_str = DIFFICULTY_NAMES.get(target_difficulty, target_difficulty.value)
    msg = f"Level {level_display} {diff_str} charts ({len(results)} songs)\n\n"
    
    for i, (song, chart) in enumerate(results[:20], 1):
        type_str = "DX" if chart.type == SongType.DX else ""
        msg += f"{i}. {song.title} {type_str}\n"
    
    if len(results) > 20:
        msg += f"\n... and {len(results) - 20} more"
    
    await level_list.finish(msg.strip())

help_cmd = on_command("help", priority=5, block=True, rule=check_blacklist)

@help_cmd.handle()
async def handle_help():
    help_text = """maimai Random Song Bot

Commands:

[Song Selection]
rs - Random song (default: Master)
rs [level] - Random song at level (e.g. rs 14, rs 14+, rs 14.5)
rs [difficulty] [level] - Specify difficulty
rs dx [level] - Random DX chart
rs utage - Random Utage chart

Level input:
- Integer (14): 14.0-14.5
- Plus (14+): 14.6-14.9
- Decimal (14.5): exact match +/- 0.05

Difficulty keywords:
easy/basic/advanced/expert/master/remaster/utage

[Search]
search [keyword] - Search song info

[Level List]
level [level] - View songs at level
level [level] [difficulty] - By difficulty

Version: Alpha-0.0.3
Songs: 1454
"""
    await help_cmd.finish(help_text)
