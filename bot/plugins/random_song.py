import sys
from pathlib import Path
# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nonebot import on_command, on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, Event, MessageSegment
from nonebot.params import CommandArg
from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType, parse_level_input, get_diving_fish_client
from core.group_blacklist import group_blacklist
from core.user_tokens import user_token_manager
from config.settings import settings

# 封面图片基础URL
COVER_BASE_URL = "https://shama.dxrating.net/images/cover/v2"


def get_cover_url(image_name: str) -> str:
    """获取歌曲封面图片URL
    
    Args:
        image_name: 图片文件名
        
    Returns:
        完整的封面图片URL
    """
    return f"{COVER_BASE_URL}/{image_name}.jpg"


# 初始化歌曲管理器和选择器
song_manager = SongManager()
song_selector = SongSelector(song_manager)

# 难度名称映射
DIFFICULTY_NAMES = {
    Difficulty.EASY: "Easy",
    Difficulty.BASIC: "Basic",
    Difficulty.ADVANCED: "Advanced",
    Difficulty.EXPERT: "Expert",
    Difficulty.MASTER: "Master",
    Difficulty.RE_MASTER: "Re:Master",
    Difficulty.UTAGE: "Utage",
}

# 歌曲类型名称映射
TYPE_NAMES = {
    SongType.STANDARD: "std",
    SongType.DX: "DX",
    SongType.UTAGE: "Utage",
}


async def check_blacklist(event: Event) -> bool:
    """检查群聊是否在黑名单中
    
    Args:
        event: 事件对象
        
    Returns:
        如果不在黑名单中返回True，否则返回False
    """
    if isinstance(event, GroupMessageEvent):
        return not group_blacklist.is_blocked(event.group_id)
    return True


def is_superuser(user_id: int) -> bool:
    """检查用户是否为超级用户
    
    Args:
        user_id: 用户QQ号
        
    Returns:
        如果是超级用户返回True，否则返回False
    """
    return str(user_id) in settings.BOT_SUPERUSERS


# 注册debug命令（仅超级用户可用）
debug_cmd = on_command("debug", aliases={"dbg"}, priority=10, block=True)


@debug_cmd.handle()
async def handle_debug(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """处理debug命令，仅超级用户可用
    
    Args:
        bot: 机器人实例
        event: 群聊消息事件
        args: 命令参数
    """
    user_id = event.user_id
    
    if not is_superuser(user_id):
        await debug_cmd.finish("此命令仅管理员可用。")
    
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    
    print(f"[DEBUG] debug called by superuser {user_id} with args: {parts}")
    
    criteria = SelectionCriteria(count=1)
    target_difficulty = None
    target_type = None
    has_difficulty_arg = False
    has_level_arg = False
    utage_only = False
    
    for part in parts:
        part_lower = part.lower()
        
        if part_lower in ["宴", "宴会场", "utage"]:
            utage_only = True
        elif part_lower in ["dx", "std"]:
            criteria.song_type = SongType.DX if part_lower == "dx" else SongType.STANDARD
            target_type = criteria.song_type
        elif part_lower in ["easy", "ez"]:
            target_difficulty = Difficulty.EASY
            has_difficulty_arg = True
        elif part_lower in ["basic", "bs", "b"]:
            target_difficulty = Difficulty.BASIC
            has_difficulty_arg = True
        elif part_lower in ["advanced", "adv", "a"]:
            target_difficulty = Difficulty.ADVANCED
            has_difficulty_arg = True
        elif part_lower in ["expert", "exp", "e"]:
            target_difficulty = Difficulty.EXPERT
            has_difficulty_arg = True
        elif part_lower in ["master", "mas", "m"]:
            target_difficulty = Difficulty.MASTER
            has_difficulty_arg = True
        elif part_lower in ["remaster", "rem", "r"]:
            target_difficulty = Difficulty.RE_MASTER
            has_difficulty_arg = True
        elif part_lower in ["utage", "u"]:
            target_difficulty = Difficulty.UTAGE
            criteria.song_type = SongType.UTAGE
            target_type = SongType.UTAGE
            has_difficulty_arg = True
            utage_only = True
        else:
            min_lv, max_lv = parse_level_input(part)
            if min_lv is not None:
                criteria.min_level = min_lv
                criteria.max_level = max_lv
                has_level_arg = True
    
    if has_level_arg and not has_difficulty_arg:
        criteria.difficulty = None
    else:
        criteria.difficulty = target_difficulty if target_difficulty is not None else Difficulty.MASTER
    
    criteria.utage_only = utage_only
    
    print(f"[DEBUG] criteria: difficulty={criteria.difficulty}, min_level={criteria.min_level}, max_level={criteria.max_level}, song_type={criteria.song_type}, utage_only={criteria.utage_only}")
    
    result = song_selector.select_random(criteria)
    print(f"[DEBUG] select_random: {len(result.songs)} songs selected, {result.total_available} total available")
    print(f"[DEBUG] all songs in pool: {[s.title for s in song_selector.get_all_songs()[:10]]}...")
    print(f"[DEBUG] filtering applied: utage_only={utage_only}, difficulty={criteria.difficulty}, level_range=({criteria.min_level}, {criteria.max_level})")
    
    if result.songs:
        song = result.songs[0]
        print(f"[DEBUG] selected song: {song.title} (id={song.id}), genre={song.genre}, type={song.type}")
        print(f"[DEBUG] song charts: {[(c.type, c.difficulty, c.level) for c in song.charts]}")
    
    await debug_cmd.finish(f"[DEBUG] 筛选条件: utage_only={utage_only}, difficulty={criteria.difficulty}, level=({criteria.min_level}, {criteria.max_level}), song_type={criteria.song_type}\n可选歌曲数量: {result.total_available}")


# 注册随机歌曲命令
random_song = on_command("random_song", aliases={"rs"}, priority=5, block=True, rule=check_blacklist)


@random_song.handle()
async def handle_random_song(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """处理随机歌曲命令
    
    Args:
        bot: 机器人实例
        event: 群聊消息事件
        args: 命令参数
    """
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    print(f"[DEBUG] rs called with arg_text: '{arg_text}'")
    print(f"[DEBUG] parts: {parts}")
    
    # 初始化选择条件
    criteria = SelectionCriteria(count=1)
    target_difficulty = None
    target_type = None
    has_difficulty_arg = False
    has_level_arg = False
    utage_only = False
    
    # 解析命令参数
    for part in parts:
        part_lower = part.lower()
        print(f"[DEBUG] processing part: '{part}' (lower: '{part_lower}')")
        
        # 处理宴会场参数
        if part_lower in ["宴", "宴会场", "utage"]:
            utage_only = True
            print(f"[DEBUG] set utage_only to: True")
        # 处理歌曲类型参数
        elif part_lower in ["dx", "std"]:
            criteria.song_type = SongType.DX if part_lower == "dx" else SongType.STANDARD
            target_type = criteria.song_type
            print(f"[DEBUG] set song_type to: {criteria.song_type}")
        # 处理难度参数
        elif part_lower in ["easy", "ez"]:
            target_difficulty = Difficulty.EASY
            has_difficulty_arg = True
            print(f"[DEBUG] set difficulty to: EASY")
        elif part_lower in ["basic", "bs", "b"]:
            target_difficulty = Difficulty.BASIC
            has_difficulty_arg = True
            print(f"[DEBUG] set difficulty to: BASIC")
        elif part_lower in ["advanced", "adv", "a"]:
            target_difficulty = Difficulty.ADVANCED
            has_difficulty_arg = True
            print(f"[DEBUG] set difficulty to: ADVANCED")
        elif part_lower in ["expert", "exp", "e"]:
            target_difficulty = Difficulty.EXPERT
            has_difficulty_arg = True
            print(f"[DEBUG] set difficulty to: EXPERT")
        elif part_lower in ["master", "mas", "m"]:
            target_difficulty = Difficulty.MASTER
            has_difficulty_arg = True
            print(f"[DEBUG] set difficulty to: MASTER")
        elif part_lower in ["remaster", "rem", "r"]:
            target_difficulty = Difficulty.RE_MASTER
            has_difficulty_arg = True
            print(f"[DEBUG] set difficulty to: RE_MASTER")
        elif part_lower in ["utage", "u"]:
            target_difficulty = Difficulty.UTAGE
            criteria.song_type = SongType.UTAGE
            target_type = SongType.UTAGE
            has_difficulty_arg = True
            utage_only = True  # 当指定UTAGE难度时，也应该只从宴会场选择
            print(f"[DEBUG] set difficulty to: UTAGE, song_type to: UTAGE, utage_only to: True")
        # 处理等级参数
        else:
            min_lv, max_lv = parse_level_input(part)
            print(f"[DEBUG] parse_level_input('{part}') returned: min={min_lv}, max={max_lv}")
            if min_lv is not None:
                criteria.min_level = min_lv
                criteria.max_level = max_lv
                has_level_arg = True
                print(f"[DEBUG] set min_level={min_lv}, max_level={max_lv}")
    
    # 设置难度条件
    if has_level_arg and not has_difficulty_arg:
        criteria.difficulty = None
        print(f"[DEBUG] set criteria.difficulty to None (has_level_arg=True, has_difficulty_arg=False)")
    else:
        criteria.difficulty = target_difficulty if target_difficulty is not None else Difficulty.MASTER
        print(f"[DEBUG] set criteria.difficulty to: {criteria.difficulty}")
    
    # 设置宴会场过滤
    criteria.utage_only = utage_only
    
    print(f"[DEBUG] Final criteria: difficulty={criteria.difficulty}, min_level={criteria.min_level}, max_level={criteria.max_level}, song_type={criteria.song_type}, utage_only={criteria.utage_only}")
    
    # 随机选择歌曲
    result = song_selector.select_random(criteria)
    print(f"[DEBUG] select_random result: {len(result.songs)} songs, {result.total_available} available")
    
    if result.songs:
        song = result.songs[0]
        msg = f"Random Song Result\n\n"
        msg += f"Title: {song.title}\n"
        msg += f"Artist: {song.artist}\n"
        
        if song.genre:
            msg += f"Genre: {song.genre}\n"
        
        msg += f"BPM: {song.bpm}\n"
        
        # 获取歌曲版本信息
        first_version = song.version
        if not first_version and song.charts:
            versions = [c.version for c in song.charts if c.version]
            if versions:
                first_version = versions[0]
        
        if first_version:
            msg += f"Version: {first_version}\n"
        
        # 处理谱面信息
        matching_charts = []
        display_difficulty = target_difficulty if has_difficulty_arg else Difficulty.MASTER
        
        # 难度到level_index的映射
        difficulty_to_level_index = {
            Difficulty.BASIC: 0,
            Difficulty.ADVANCED: 1,
            Difficulty.EXPERT: 2,
            Difficulty.MASTER: 3,
            Difficulty.RE_MASTER: 4,
            Difficulty.UTAGE: 3  # 宴会场难度使用master的索引
        }
        
        # 当指定了等级但未指定难度时，查找所有符合等级的谱面
        if has_level_arg and not has_difficulty_arg:
            for chart in song.charts:
                if target_type and chart.type != target_type:
                    continue
                
                # 获取谱面等级
                level = chart.internal_level
                if level is None:
                    try:
                        level_str = chart.level.replace("+", ".7")
                        level = float(level_str)
                    except ValueError:
                        continue
                
                if level is None:
                    continue
                
                # 检查等级范围
                if criteria.min_level is not None and level < criteria.min_level:
                    continue
                if criteria.max_level is not None and level > criteria.max_level:
                    continue
                
                matching_charts.append(chart)
        else:
            # 当指定了难度时，查找符合难度和等级的谱面
            for chart in song.charts:
                if target_type and chart.type != target_type:
                    continue
                if chart.difficulty == display_difficulty:
                    # 检查等级范围（如果指定了等级）
                    if has_level_arg:
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
                    matching_charts.append(chart)
        
        if matching_charts:
            chart = matching_charts[0]
            type_str = TYPE_NAMES.get(chart.type, chart.type.value)
            diff_str = DIFFICULTY_NAMES.get(chart.difficulty, chart.difficulty.value)
            level_display = chart.level
            if chart.internal_level:
                level_display += f" ({chart.internal_level:.1f})"
            
            # 使用谱面ID（直接使用真实ID）
            chart_id = chart.id
            
            msg += f"\n[{type_str}] {diff_str} {level_display} (ID: {chart_id})\n"
            
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
        
        # 显示歌曲别名
        if song.alias and len(song.alias) > 0:
            aliases_str = ", ".join(song.alias[:3])
            if len(song.alias) > 3:
                aliases_str += "..."
            msg += f"\nAlias: {aliases_str}\n"
        
        msg += f"\nFound {result.total_available} matching songs"
        
        # 尝试获取用户成绩
        user_token = user_token_manager.get_token(event.user_id)
        if user_token and matching_charts:
            client = get_diving_fish_client()
            if client:
                try:
                    chart = matching_charts[0]
                    song_type = "DX" if chart.type == SongType.DX else "SD"
                    diff_name = DIFFICULTY_NAMES.get(chart.difficulty, "Master").lower()
                    score = await client.get_song_score_by_name(
                        user_token.diving_fish_username,
                        song.title,
                        diff_name,
                        song_type,
                        user_token.import_token
                    )
                    if score:
                        msg += f"\n\n--- Your Score ---"
                        msg += f"\n达成率: {score.achievement:.4f}%"
                        msg += f"\nDX Score: {score.dx_score}/{score.dx_score_max}"
                        if score.fc:
                            fc_names = {"fc": "FC", "fcplus": "FC+", "ap": "AP", "applus": "AP+"}
                            msg += f" | {fc_names.get(score.fc.lower(), score.fc)}"
                        if score.fs:
                            fs_names = {"fs": "FS", "fsplus": "FS+", "fsd": "FSD", "fsdplus": "FSD+"}
                            msg += f" | {fs_names.get(score.fs.lower(), score.fs)}"
                        if score.rate:
                            rate_names = {"d": "D", "c": "C", "b": "B", "bb": "BB", "bbb": "BBB", 
                                          "a": "A", "aa": "AA", "aaa": "AAA", "s": "S", "sp": "S+", 
                                          "ss": "SS", "ssp": "SS+", "sss": "SSS", "sssp": "SSS+"}
                            msg += f"\n评价: {rate_names.get(score.rate.lower(), score.rate)}"
                except Exception:
                    pass
        
        # 发送消息（包含图片）
        try:
            if song.image_url:
                cover_url = get_cover_url(song.image_url)
                await random_song.send(Message(msg + MessageSegment.image(cover_url)))
            else:
                await random_song.send(msg)
        except Exception:
            await random_song.send(msg)
    else:
        await random_song.finish("No matching songs found. Try adjusting your criteria.")


# 注册搜索歌曲命令
search_song = on_command("search", aliases={"find"}, priority=5, block=True, rule=check_blacklist)


@search_song.handle()
async def handle_search_song(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """处理搜索歌曲命令
    
    Args:
        bot: 机器人实例
        event: 群聊消息事件
        args: 命令参数
    """
    keyword = args.extract_plain_text().strip()
    
    if not keyword:
        await search_song.finish("Please enter a song name or alias to search")
    
    # 搜索歌曲
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
        # 显示单个搜索结果
        song = results[0]
        msg = f"Search Result\n\n"
        msg += f"Title: {song.title}\n"
        msg += f"Artist: {song.artist}\n"
        
        if song.genre:
            msg += f"Genre: {song.genre}\n"
        
        msg += f"BPM: {song.bpm}\n"
        msg += f"Type: {TYPE_NAMES.get(song.type, song.type.value)}\n"
        
        # 获取歌曲版本信息
        first_version = song.version
        if not first_version and song.charts:
            versions = [c.version for c in song.charts if c.version]
            if versions:
                first_version = versions[0]
        
        if first_version:
            msg += f"Version: {first_version}\n"
        
        # 显示谱面列表
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
        
        # 显示别名
        if song.alias and len(song.alias) > 0:
            msg += f"\nAlias: {', '.join(song.alias)}\n"
        
        # 发送消息（包含图片）
        try:
            if song.image_url:
                cover_url = get_cover_url(song.image_url)
                await search_song.send(Message(msg.strip() + MessageSegment.image(cover_url)))
            else:
                await search_song.send(msg.strip())
        except Exception:
            await search_song.send(msg.strip())
    else:
        # 显示多个搜索结果
        msg = f"Found {len(results)} related songs:\n\n"
        for i, song in enumerate(results[:10], 1):
            msg += f"{i}. {song.title} - {song.artist}\n"
        
        if len(results) > 10:
            msg += f"\n... and {len(results) - 10} more"
        
        await search_song.finish(msg.strip())


# 注册等级列表命令
level_list = on_command("level", aliases={"lv"}, priority=5, block=True, rule=check_blacklist)


@level_list.handle()
async def handle_level_list(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    """处理等级列表命令
    
    Args:
        bot: 机器人实例
        event: 群聊消息事件
        args: 命令参数
    """
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    
    min_level = None
    max_level = None
    target_difficulty = Difficulty.MASTER
    level_display = None
    
    # 解析命令参数
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
    
    # 查找符合条件的歌曲
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
    
    # 排序并显示结果
    results.sort(key=lambda x: x[0].title)
    
    diff_str = DIFFICULTY_NAMES.get(target_difficulty, target_difficulty.value)
    msg = f"Level {level_display} {diff_str} charts ({len(results)} songs)\n\n"
    
    for i, (song, chart) in enumerate(results[:20], 1):
        type_str = "DX" if chart.type == SongType.DX else ""
        msg += f"{i}. {song.title} {type_str}\n"
    
    if len(results) > 20:
        msg += f"\n... and {len(results) - 20} more"
    
    await level_list.finish(msg.strip())


# 注册帮助命令
help_cmd = on_command("help", priority=5, block=True, rule=check_blacklist)


@help_cmd.handle()
async def handle_help():
    """处理帮助命令"""
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
