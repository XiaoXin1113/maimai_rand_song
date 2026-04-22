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
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    if parts and parts[0].lower() == "help":
        help_msg = "debug命令帮助\n\n"
        help_msg += "使用方法: /debug <指令> [参数]\n\n"
        help_msg += "说明:\n"
        help_msg += "- 该命令仅超级用户可用\n"
        help_msg += "- 用于调试其他命令的执行过程\n\n"
        help_msg += "支持的指令:\n"
        help_msg += "- rs - 调试随机歌曲命令\n"
        help_msg += "- score - 调试查分命令\n"
        help_msg += "- search - 调试搜索命令\n"
        help_msg += "- level - 调试等级列表命令\n\n"
        help_msg += "示例:\n"
        help_msg += "/debug rs - 调试 rs 命令\n"
        help_msg += "/debug score - 调试 score 命令\n"
        help_msg += "/debug score -id 11307 - 调试按ID查询成绩\n"
        help_msg += "/debug search Yorugao - 调试搜索命令\n"
        help_msg += "/debug search 11307 - 调试按ID搜索\n"
        help_msg += "/debug level 14 - 调试等级列表命令\n"
        await debug_cmd.finish(help_msg)
    
    debug_output = f"[DEBUG] 命令调用: /debug {' '.join(parts)}\n"
    print(f"[DEBUG] debug called by superuser {user_id} with args: {parts}")
    
    if not parts:
        await debug_cmd.finish("[DEBUG] 请指定要调试的指令，例如: /debug rs\n使用 /debug help 查看详细帮助")
    
    # 获取指令名称
    cmd_name = parts[0].lower()
    cmd_args = parts[1:] if len(parts) > 1 else []
    
    debug_output += f"[DEBUG] 指令: {cmd_name}\n"
    debug_output += f"[DEBUG] 参数: {cmd_args}\n"
    
    if cmd_name == "rs":
        # 调试 rs 命令
        criteria = SelectionCriteria(count=1)
        target_difficulty = None
        target_type = None
        has_difficulty_arg = False
        has_level_arg = False
        utage_only = False
        
        for part in cmd_args:
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
        
        debug_output += f"[DEBUG] 筛选条件: difficulty={criteria.difficulty}, min_level={criteria.min_level}, max_level={criteria.max_level}, song_type={criteria.song_type}, utage_only={criteria.utage_only}\n"
        
        import io
        import sys
        from contextlib import redirect_stdout
        
        # 捕获所有控制台输出
        f = io.StringIO()
        with redirect_stdout(f):
            result = song_selector.select_random(criteria)
            console_output = f.getvalue()
        
        if console_output:
            debug_output += f"[CONSOLE] {console_output}\n"
        
        debug_output += f"[DEBUG] 可选歌曲数量: {result.total_available}\n"
        
        if result.songs:
            song = result.songs[0]
            debug_output += f"[DEBUG] 选中歌曲: {song.title} (id={song.id}), genre={song.genre}, type={song.type}\n"
            debug_output += f"[DEBUG] 谱面信息: {[(c.type, c.difficulty, c.level) for c in song.charts]}\n"
        else:
            debug_output += f"[DEBUG] 没有找到匹配的歌曲\n"
        
        await debug_cmd.finish(debug_output)
    elif cmd_name == "score":
        # 调试 score 命令
        # 避免导入diving_fish模块，防止插件重复加载
        debug_output += f"[DEBUG] 开始处理 score 命令\n"
        
        # 解析参数
        parts = cmd_args
        query_type = "auto"
        query_value = ""
        target_difficulty = "master"
        target_type = "DX"
        
        i = 0
        while i < len(parts):
            part = parts[i]
            part_lower = part.lower()
            
            if part == "-n":
                query_type = "name"
                query_value = " ".join(parts[i+1:])
                break
            elif part == "-id":
                query_type = "id"
                if i + 1 < len(parts):
                    query_value = parts[i+1]
                break
            elif part_lower in ["basic", "bs", "b"]:
                target_difficulty = "basic"
            elif part_lower in ["advanced", "adv", "a"]:
                target_difficulty = "advanced"
            elif part_lower in ["expert", "exp", "e"]:
                target_difficulty = "expert"
            elif part_lower in ["master", "mas", "m"]:
                target_difficulty = "master"
            elif part_lower in ["remaster", "rem", "r"]:
                target_difficulty = "remaster"
            elif part_lower in ["dx", "std"]:
                target_type = "DX" if part_lower == "dx" else "SD"
            else:
                if query_type == "auto":
                    query_value = " ".join(parts)
            i += 1
        
        # 处理自动模式
        if query_type == "auto":
            if query_value.isdigit():
                query_type = "id"
            else:
                query_type = "name"
        
        debug_output += f"[DEBUG] 查询类型: {query_type}\n"
        debug_output += f"[DEBUG] 查询值: {query_value}\n"
        debug_output += f"[DEBUG] 目标难度: {target_difficulty}\n"
        debug_output += f"[DEBUG] 目标类型: {target_type}\n"
        
        # 执行查询
        import io
        import sys
        from contextlib import redirect_stdout
        
        # 捕获所有控制台输出
        f = io.StringIO()
        with redirect_stdout(f):
            if query_type == "id":
                try:
                    song_id = int(query_value)
                    # 模拟查询结果
                    debug_output += f"[DEBUG] 按ID查询结果: 1 个匹配\n"
                    debug_output += f"[DEBUG] 1. 模拟歌曲 (ID: {song_id}, 相似度: 1.00)\n"
                except ValueError:
                    debug_output += f"[DEBUG] 无效的谱面ID\n"
            else:
                # 模拟查询结果
                debug_output += f"[DEBUG] 按歌名查询结果: 1 个匹配\n"
                debug_output += f"[DEBUG] 1. 模拟歌曲 (ID: 12345, 相似度: 0.85)\n"
            console_output = f.getvalue()
        
        if console_output:
            debug_output += f"[CONSOLE] {console_output}\n"
        
        # 模拟API调用
        debug_output += f"[DEBUG] 模拟API调用: 获取歌曲成绩\n"
        debug_output += f"[DEBUG] 模拟返回成绩数据\n"
        
        await debug_cmd.finish(debug_output)
    elif cmd_name == "search":
        # 调试 search 命令
        debug_output += f"[DEBUG] 开始处理 search 命令\n"
        
        # 解析参数
        parts = cmd_args
        is_id_search = False
        chart_id = None
        keyword = " ".join(parts)
        
        if len(parts) >= 2 and parts[0] == "-id":
            is_id_search = True
            chart_id_str = parts[1]
            if chart_id_str.isdigit():
                chart_id = int(chart_id_str)
        elif len(parts) == 1 and parts[0].isdigit():
            is_id_search = True
            chart_id = int(parts[0])
        else:
            keyword = " ".join(parts)
        
        debug_output += f"[DEBUG] ID搜索: {is_id_search}\n"
        debug_output += f"[DEBUG] 谱面ID: {chart_id}\n"
        debug_output += f"[DEBUG] 关键词: {keyword}\n"
        
        # 执行搜索
        import io
        import sys
        from contextlib import redirect_stdout
        
        # 捕获所有控制台输出
        f = io.StringIO()
        with redirect_stdout(f):
            all_songs = song_manager.get_all_songs()
            debug_output += f"[DEBUG] 歌曲库加载完成，共 {len(all_songs)} 首歌曲\n"
            
            if is_id_search and chart_id:
                # 按ID搜索
                found = False
                for song in all_songs:
                    for chart in song.charts:
                        if chart.id == chart_id:
                            debug_output += f"[DEBUG] 找到谱面: ID={chart.id}, 歌曲={song.title}, 难度={chart.difficulty.value}\n"
                            found = True
                            break
                    if found:
                        break
                if not found:
                    debug_output += f"[DEBUG] 未找到ID为 {chart_id} 的谱面\n"
            elif keyword:
                # 按关键词搜索
                results = []
                for song in all_songs:
                    if keyword.lower() in song.title.lower() or any(keyword.lower() in alias.lower() for alias in song.alias):
                        results.append(song)
                debug_output += f"[DEBUG] 搜索结果: {len(results)} 首歌曲\n"
                for song in results[:5]:  # 只显示前5个结果
                    debug_output += f"[DEBUG] 结果: {song.title} - {song.artist}\n"
                if len(results) > 5:
                    debug_output += f"[DEBUG] ... 还有 {len(results) - 5} 个结果\n"
            console_output = f.getvalue()
        
        if console_output:
            debug_output += f"[CONSOLE] {console_output}\n"
        
        await debug_cmd.finish(debug_output)
    elif cmd_name == "level":
        # 调试 level 命令
        debug_output += f"[DEBUG] 开始处理 level 命令\n"
        
        # 解析参数
        parts = cmd_args
        min_level = None
        max_level = None
        target_difficulty = Difficulty.MASTER
        
        for arg in parts:
            arg_lower = arg.lower()
            if arg_lower in ["master", "mas", "m"]:
                target_difficulty = Difficulty.MASTER
            elif arg_lower in ["remaster", "rem", "r"]:
                target_difficulty = Difficulty.RE_MASTER
            elif arg_lower in ["expert", "exp", "e"]:
                target_difficulty = Difficulty.EXPERT
            else:
                min_lv, max_lv = parse_level_input(arg)
                if min_lv is not None:
                    min_level = min_lv
                    max_level = max_lv
        
        debug_output += f"[DEBUG] 难度: {target_difficulty.value}\n"
        debug_output += f"[DEBUG] 最低等级: {min_level}\n"
        debug_output += f"[DEBUG] 最高等级: {max_level}\n"
        
        # 执行等级列表查询
        import io
        import sys
        from contextlib import redirect_stdout
        
        # 捕获所有控制台输出
        f = io.StringIO()
        with redirect_stdout(f):
            all_songs = song_manager.get_all_songs()
            results = []
            
            for song in all_songs:
                for chart in song.charts:
                    if chart.difficulty == target_difficulty and chart.internal_level:
                        if min_level is not None and max_level is not None:
                            if min_level <= chart.internal_level <= max_level:
                                results.append((song, chart))
                        else:
                            results.append((song, chart))
            
            debug_output += f"[DEBUG] 等级列表结果: {len(results)} 个谱面\n"
            for song, chart in results[:5]:  # 只显示前5个结果
                level_display = chart.level
                if chart.internal_level:
                    level_display += f"({chart.internal_level:.1f})"
                debug_output += f"[DEBUG] 结果: {song.title} - {level_display}\n"
            if len(results) > 5:
                debug_output += f"[DEBUG] ... 还有 {len(results) - 5} 个结果\n"
            console_output = f.getvalue()
        
        if console_output:
            debug_output += f"[CONSOLE] {console_output}\n"
        
        await debug_cmd.finish(debug_output)
    else:
        await debug_cmd.finish(f"[DEBUG] 不支持的指令: {cmd_name}")


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
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    if parts and parts[0].lower() == "help":
        help_msg = "随机歌曲命令帮助\n\n"
        help_msg += "使用方法: /rs [参数]\n\n"
        help_msg += "参数说明:\n"
        help_msg += "- 难度参数: easy/ez, basic/bs/b, advanced/adv/a, expert/exp/e, master/mas/m, remaster/rem/r, utage/u\n"
        help_msg += "- 类型参数: dx, std\n"
        help_msg += "- 等级参数: 例如 13, 13+, 14-15 等\n"
        help_msg += "- 特殊参数: 宴/宴会场/utage (只随机宴会歌曲)\n\n"
        help_msg += "示例:\n"
        help_msg += "/rs - 随机一首 Master 难度的歌曲\n"
        help_msg += "/rs master - 随机一首 Master 难度的歌曲\n"
        help_msg += "/rs dx - 随机一首 DX 类型的歌曲\n"
        help_msg += "/rs 13+ - 随机一首等级 13+ 的歌曲\n"
        help_msg += "/rs expert 14-15 - 随机一首 Expert 难度、等级 14-15 的歌曲\n"
        await random_song.finish(help_msg)
    
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
    arg_text = args.extract_plain_text().strip()
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    parts = arg_text.split() if arg_text else []
    if parts and parts[0].lower() == "help":
        help_msg = "搜索命令帮助\n\n"
        help_msg += "使用方法: /search [参数] <关键词>\n\n"
        help_msg += "参数说明:\n"
        help_msg += "- -id <谱面ID> - 按谱面ID搜索\n\n"
        help_msg += "说明:\n"
        help_msg += "- 该命令用于搜索歌曲信息\n"
        help_msg += "- 可以使用歌曲名称或别名为关键词\n"
        help_msg += "- 直接输入数字时默认按ID搜索\n"
        help_msg += "- 搜索置信度为50%，满足此置信度的均加入结果列表\n\n"
        help_msg += "示例:\n"
        help_msg += "/search Yorugao - 搜索歌曲 'Yorugao'\n"
        help_msg += "/search 夜想曲 - 搜索歌曲 '夜想曲'\n"
        help_msg += "/search 11307 - 搜索谱面ID为 11307 的谱面\n"
        help_msg += "/search -id 11307 - 搜索谱面ID为 11307 的谱面\n"
        await search_song.finish(help_msg)
    
    if not arg_text:
        await search_song.finish("Please enter a song name or alias to search\n使用 /search help 查看详细帮助")
    
    # 解析参数
    parts = arg_text.split()
    is_id_search = False
    chart_id = None
    keyword = arg_text
    
    if len(parts) >= 2 and parts[0] == "-id":
        is_id_search = True
        chart_id_str = parts[1]
        if chart_id_str.isdigit():
            chart_id = int(chart_id_str)
        else:
            await search_song.finish("Invalid chart ID. Please enter a valid number.")
    elif arg_text.isdigit():
        # 直接输入数字时默认按ID搜索
        is_id_search = True
        chart_id = int(arg_text)
    else:
        # 普通搜索模式
        keyword = arg_text
    
    if is_id_search:
        # 按谱面ID搜索
        all_songs = song_manager.get_all_songs()
        found_song = None
        
        for song in all_songs:
            for chart in song.charts:
                if chart.id == chart_id:
                    found_song = song
                    break
            if found_song:
                break
        
        if found_song:
            # 显示歌曲信息和所有难度
            msg = f"Search Result\n\n"
            msg += f"Title: {found_song.title}\n"
            msg += f"Artist: {found_song.artist}\n"
            
            if found_song.genre:
                msg += f"Genre: {found_song.genre}\n"
            
            msg += f"BPM: {found_song.bpm}\n"
            
            # 获取歌曲版本信息
            first_version = found_song.version
            if not first_version and found_song.charts:
                versions = [c.version for c in found_song.charts if c.version]
                if versions:
                    first_version = versions[0]
            
            if first_version:
                msg += f"Version: {first_version}\n"
            
            # 显示谱面列表（所有难度）
            msg += f"\nDifficulty List:\n"
            
            chart_groups = {}
            for c in found_song.charts:
                key = c.type.value
                if key not in chart_groups:
                    chart_groups[key] = []
                chart_groups[key].append(c)
            
            for chart_type in [SongType.STANDARD, SongType.DX, SongType.UTAGE]:
                if chart_type.value in chart_groups:
                    type_str = TYPE_NAMES.get(chart_type, chart_type.value)
                    chart_id = chart_groups[chart_type.value][0].id
                    msg += f"\n[{type_str}] (ID: {chart_id})\n"
                    for c in sorted(chart_groups[chart_type.value], key=lambda c: list(Difficulty).index(c.difficulty)):
                        diff_str = DIFFICULTY_NAMES.get(c.difficulty, c.difficulty.value)
                        level_display = c.level
                        if c.internal_level:
                            level_display += f"({c.internal_level:.1f})"
                        msg += f"  {diff_str}: {level_display} (ID: {c.id})\n"
                        if c.note_counts:
                            msg += f"    Notes: {c.note_counts.total} (Tap: {c.note_counts.tap}, Hold: {c.note_counts.hold}, Slide: {c.note_counts.slide}, Touch: {c.note_counts.touch}, Break: {c.note_counts.break_note})\n"
            
            # 显示别名
            if found_song.alias and len(found_song.alias) > 0:
                msg += f"\nAlias: {', '.join(found_song.alias)}\n"
            
            # 发送消息（包含图片）
            try:
                if found_song.image_url:
                    cover_url = get_cover_url(found_song.image_url)
                    await search_song.send(Message(msg.strip() + MessageSegment.image(cover_url)))
                else:
                    await search_song.send(msg.strip())
            except Exception:
                await search_song.send(msg.strip())
        else:
            await search_song.finish(f"No chart found with ID: {chart_id}")
    else:
        # 普通搜索模式
        all_songs = song_manager.get_all_songs()
        results = []
        
        # 计算Levenshtein距离的函数
        def levenshtein_distance(s1, s2):
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            return previous_row[-1]
        
        # 计算匹配相似度
        def calculate_similarity(text, keyword):
            text_lower = text.lower()
            keyword_lower = keyword.lower()
            
            # 完全匹配
            if keyword_lower == text_lower:
                return 1.0
            
            # 子串匹配
            if keyword_lower in text_lower:
                return 0.8 + (0.2 * (len(keyword_lower) / len(text_lower)))
            
            # Levenshtein距离匹配
            distance = levenshtein_distance(text_lower, keyword_lower)
            max_len = max(len(text_lower), len(keyword_lower))
            if max_len == 0:
                return 0.0
            similarity = 1.0 - (distance / max_len)
            return similarity
        
        # 搜索歌曲
        for song in all_songs:
            # 计算标题匹配度
            title_similarity = calculate_similarity(song.title, keyword)

            # 计算别名匹配度
            alias_similarity = 0.0
            for alias in song.alias:
                sim = calculate_similarity(alias, keyword)
                if sim > alias_similarity:
                    alias_similarity = sim

            # 取最大匹配度
            max_similarity = max(title_similarity, alias_similarity)

            # 置信度阈值设为50%
            if max_similarity >= 0.5:
                results.append((song, title_similarity, alias_similarity, max_similarity))

        # 按相似度排序
        results.sort(key=lambda x: x[3], reverse=True)

        if not results:
            await search_song.finish(f"No songs found containing \"{keyword}\"")

        # 检查是否有歌名100%匹配的结果
        title_100_results = [r for r in results if r[1] == 1.0]

        # 去重，确保每个歌曲只显示一次
        unique_results = []
        seen_titles = set()
        for song, title_sim, alias_sim, max_sim in results:
            if song.title not in seen_titles:
                seen_titles.add(song.title)
                unique_results.append((song, title_sim, alias_sim, max_sim))

        if not unique_results:
            await search_song.finish(f"No songs found containing \"{keyword}\"")

        if len(unique_results) == 1:
            song = unique_results[0][0]
            msg = f"Search Result\n\n"
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
            
            # 显示谱面列表
            msg += f"\nDifficulty List:\n"
            
            chart_groups = {}
            for c in song.charts:
                key = c.type.value
                if key not in chart_groups:
                    chart_groups[key] = []
                chart_groups[key].append(c)
            
            for chart_type in [SongType.STANDARD, SongType.DX, SongType.UTAGE]:
                if chart_type.value in chart_groups:
                    type_str = TYPE_NAMES.get(chart_type, chart_type.value)
                    chart_id = chart_groups[chart_type.value][0].id
                    msg += f"\n[{type_str}] (ID: {chart_id})\n"
                    for c in sorted(chart_groups[chart_type.value], key=lambda c: list(Difficulty).index(c.difficulty)):
                        diff_str = DIFFICULTY_NAMES.get(c.difficulty, c.difficulty.value)
                        level_display = c.level
                        if c.internal_level:
                            level_display += f"({c.internal_level:.1f})"
                        msg += f"  {diff_str}: {level_display} (ID: {c.id})\n"

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
            msg = f"Found {len(unique_results)} related songs:\n\n"
            for i, (song, title_sim, alias_sim, max_sim) in enumerate(unique_results[:10], 1):
                msg += f"{i}. {song.title} - {song.artist} (相似度: {max_sim:.2f})\n"

            if len(unique_results) > 10:
                msg += f"\n... and {len(unique_results) - 10} more"

            msg += "\n\n提示: 若要查看特定歌曲的详细信息，请使用 /search <歌曲名>"

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
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    if parts and parts[0].lower() == "help":
        help_msg = "等级列表命令帮助\n\n"
        help_msg += "使用方法: /level [难度] <等级>\n\n"
        help_msg += "说明:\n"
        help_msg += "- 该命令用于查看指定等级的歌曲列表\n\n"
        help_msg += "难度参数:\n"
        help_msg += "- expert/exp/e - Expert 难度\n"
        help_msg += "- master/mas/m - Master 难度 (默认)\n"
        help_msg += "- remaster/rem/r - Re:Master 难度\n\n"
        help_msg += "等级参数格式:\n"
        help_msg += "- 整数 (14): 14.0-14.5\n"
        help_msg += "- 加号 (14+): 14.6-14.9\n"
        help_msg += "- 小数 (14.5): 精确匹配 +/- 0.05\n\n"
        help_msg += "示例:\n"
        help_msg += "/level 14 - 查看 Master 难度 14 级的歌曲\n"
        help_msg += "/level 14+ - 查看 Master 难度 14+ 级的歌曲\n"
        help_msg += "/level expert 15 - 查看 Expert 难度 15 级的歌曲\n"
        help_msg += "/level rem 16 - 查看 Re:Master 难度 16 级的歌曲\n"
        await level_list.finish(help_msg)
    
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
        await level_list.finish("Please specify a level, e.g.: level 14, level 14+, level 14.5\n使用 /level help 查看详细帮助")
    
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
async def handle_help(args: Message = CommandArg()):
    """处理帮助命令"""
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    if parts and parts[0].lower() == "help":
        help_msg = "帮助命令帮助\n\n"
        help_msg += "使用方法: /help\n\n"
        help_msg += "说明:\n"
        help_msg += "- 该命令显示所有可用命令的帮助信息\n\n"
        help_msg += "示例:\n"
        help_msg += "/help - 显示所有命令的帮助信息\n"
        await help_cmd.finish(help_msg)
    
    help_text = """maimai Random Song Bot

命令列表：

【歌曲选择】
/rs - 随机歌曲 (默认: Master)
/rs [等级] - 指定等级的随机歌曲 (例如: /rs 14, /rs 14+, /rs 14.5)
/rs [难度] [等级] - 指定难度和等级
/rs dx [等级] - 随机 DX 谱面
/rs utage - 随机宴会谱面

【查分系统】
/score <歌曲名> - 查询歌曲成绩
/score -id <谱面ID> - 按谱面ID查询
/score -d <难度> - 指定难度
/bind <Import-Token> - 绑定水鱼账号
/unbind - 解绑水鱼账号

【搜索与查询】
/search <关键词> - 搜索歌曲信息
/level [难度] <等级> - 查看指定等级的歌曲列表

【其他】
/help - 显示此帮助信息

使用方法：
- 所有命令都支持添加 help 参数查看详细帮助，例如：/rs help
- 等级格式：14 (14.0-14.5), 14+ (14.6-14.9), 14.5 (精确匹配)
- 难度关键词：easy/basic/advanced/expert/master/remaster/utage

版本: Alpha-0.0.3
作者：SeaqUs
歌曲数量: 1454
"""
    await help_cmd.finish(help_text)
