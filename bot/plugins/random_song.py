import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nonebot import on_command, on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, Event
from nonebot.params import CommandArg
from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType
from core.group_blacklist import group_blacklist

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
    SongType.STANDARD: "标准",
    SongType.DX: "DX",
    SongType.UTAGE: "Utage",
}

async def check_blacklist(event: Event) -> bool:
    if isinstance(event, GroupMessageEvent):
        return not group_blacklist.is_blocked(event.group_id)
    return True

random_song = on_command("随机选歌", aliases={"选歌"}, priority=5, block=True, rule=check_blacklist)

@random_song.handle()
async def handle_random_song(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    
    criteria = SelectionCriteria(count=1)
    target_difficulty = Difficulty.MASTER
    target_type = None
    
    for part in parts:
        part_lower = part.lower()
        
        if part_lower in ["dx", "标准", "std"]:
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
        elif part_lower in ["remaster", "rem", "r", "re:master"]:
            target_difficulty = Difficulty.RE_MASTER
        elif part_lower in ["utage", "u"]:
            target_difficulty = Difficulty.UTAGE
            criteria.song_type = SongType.UTAGE
            target_type = SongType.UTAGE
        else:
            try:
                level = float(part.replace("+", ".7"))
                criteria.min_level = level - 0.3
                criteria.max_level = level + 0.3
            except ValueError:
                pass
    
    criteria.difficulty = target_difficulty
    
    result = song_selector.select_random(criteria)
    
    if result.songs:
        song = result.songs[0]
        msg = f"🎵 随机选歌结果\n\n"
        msg += f"📌 {song.title}\n"
        msg += f"👤 {song.artist}\n"
        
        if song.genre:
            msg += f"🎭 流派：{song.genre}\n"
        
        msg += f" BPM：{song.bpm}\n"
        
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
            
            msg += f"\n📊 [{type_str}] {diff_str} {level_display}\n"
            
            if chart.note_designer:
                msg += f"✍️ 谱师：{chart.note_designer}\n"
            
            if chart.note_counts:
                nc = chart.note_counts
                msg += f"🎵 音符：Tap {nc.tap} / Hold {nc.hold} / Slide {nc.slide}"
                if nc.touch > 0:
                    msg += f" / Touch {nc.touch}"
                if nc.break_note > 0:
                    msg += f" / Break {nc.break_note}"
                msg += f" (总计 {nc.total})\n"
        
        if song.alias and len(song.alias) > 0:
            aliases_str = ", ".join(song.alias[:3])
            if len(song.alias) > 3:
                aliases_str += "..."
            msg += f"\n💡 别名：{aliases_str}\n"
        
        msg += f"\n📈 共找到 {result.total_available} 首符合条件的歌曲"
        await random_song.finish(msg)
    else:
        await random_song.finish("没有找到符合条件的歌曲，请尝试调整筛选条件")

search_song = on_command("查歌", aliases={"搜索歌曲"}, priority=5, block=True, rule=check_blacklist)

@search_song.handle()
async def handle_search_song(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    keyword = args.extract_plain_text().strip()
    
    if not keyword:
        await search_song.finish("请输入要搜索的歌曲名称或别名")
    
    all_songs = song_manager.get_all_songs()
    results = []
    
    for song in all_songs:
        if keyword.lower() in song.title.lower():
            results.append(song)
        elif any(keyword.lower() in alias.lower() for alias in song.alias):
            results.append(song)
    
    if not results:
        await search_song.finish(f"没有找到包含 \"{keyword}\" 的歌曲")
    
    if len(results) == 1:
        song = results[0]
        msg = f"🔍 查歌结果\n\n"
        msg += f"📌 {song.title}\n"
        msg += f"👤 {song.artist}\n"
        
        if song.genre:
            msg += f"🎭 流派：{song.genre}\n"
        
        msg += f" BPM：{song.bpm}\n"
        msg += f"💿 类型：{TYPE_NAMES.get(song.type, song.type.value)}\n"
        
        msg += f"\n📊 难度列表：\n"
        
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
            msg += f"\n💡 别名：{', '.join(song.alias)}\n"
        
        await search_song.finish(msg.strip())
    else:
        msg = f"🔍 找到 {len(results)} 首相关歌曲：\n\n"
        for i, song in enumerate(results[:10], 1):
            msg += f"{i}. {song.title} - {song.artist}\n"
        
        if len(results) > 10:
            msg += f"\n... 还有 {len(results) - 10} 首歌曲"
        
        await search_song.finish(msg.strip())

level_list = on_command("定数表", aliases={"等级表"}, priority=5, block=True, rule=check_blacklist)

@level_list.handle()
async def handle_level_list(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    
    target_level = None
    target_difficulty = Difficulty.MASTER
    
    for part in parts:
        part_lower = part.lower()
        
        if part_lower in ["master", "mas", "m"]:
            target_difficulty = Difficulty.MASTER
        elif part_lower in ["remaster", "rem", "r"]:
            target_difficulty = Difficulty.RE_MASTER
        elif part_lower in ["expert", "exp", "e"]:
            target_difficulty = Difficulty.EXPERT
        else:
            try:
                target_level = float(part.replace("+", ".7"))
            except ValueError:
                pass
    
    if target_level is None:
        await level_list.finish("请指定要查询的定数，例如：定数表 14.5")
    
    all_songs = song_manager.get_all_songs()
    results = []
    
    for song in all_songs:
        for chart in song.charts:
            if chart.difficulty == target_difficulty and chart.internal_level:
                if abs(chart.internal_level - target_level) < 0.1:
                    results.append((song, chart))
    
    if not results:
        await level_list.finish(f"没有找到定数为 {target_level} 的{DIFFICULTY_NAMES.get(target_difficulty, '')}谱面")
    
    results.sort(key=lambda x: x[0].title)
    
    diff_str = DIFFICULTY_NAMES.get(target_difficulty, target_difficulty.value)
    msg = f"📊 定数 {target_level} 的{diff_str}谱面 ({len(results)}首)\n\n"
    
    for i, (song, chart) in enumerate(results[:20], 1):
        type_str = "DX" if chart.type == SongType.DX else ""
        msg += f"{i}. {song.title} {type_str}\n"
    
    if len(results) > 20:
        msg += f"\n... 还有 {len(results) - 20} 首"
    
    await level_list.finish(msg.strip())

help_cmd = on_command("帮助", aliases={"help"}, priority=5, block=True, rule=check_blacklist)

@help_cmd.handle()
async def handle_help():
    help_text = """🤖 maimai随机选歌机器人

📖 指令列表：

【选歌】
随机选歌 - 随机选择一首歌曲
随机选歌 [等级] - 随机选择指定定数的歌曲
随机选歌 [等级] [难度] - 指定难度选歌
随机选歌 dx [等级] - 随机选择DX谱面
随机选歌 utage - 随机选择Utage谱面

难度关键词：
easy/basic/advanced/expert/master/remaster/utage

【查歌】
查歌 [关键词] - 搜索歌曲信息

【定数表】
定数表 [定数] - 查看指定定数的歌曲
定数表 [定数] [难度] - 查看指定难度的定数表

版本：Alpha-0.0.2
曲库：1317 首歌曲
"""
    await help_cmd.finish(help_text)
