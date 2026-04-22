import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message, Event, MessageSegment
from nonebot.params import CommandArg
from core import get_diving_fish_client, SongManager, Difficulty, SongType, song_manager
from core.user_tokens import user_token_manager
from core.group_blacklist import group_blacklist

DIFFICULTY_INDEX = {
    "basic": 0,
    "advanced": 1,
    "expert": 2,
    "master": 3,
    "remaster": 4
}

DIFFICULTY_NAMES = {
    0: "Basic",
    1: "Advanced",
    2: "Expert",
    3: "Master",
    4: "Re:Master"
}

def calculate_similarity(s1: str, s2: str) -> float:
    """计算两个字符串的相似度
    
    Args:
        s1: 第一个字符串
        s2: 第二个字符串
        
    Returns:
        相似度，范围0-1
    """
    s1 = s1.lower()
    s2 = s2.lower()
    
    # 完全匹配
    if s1 == s2:
        return 1.0
    
    # 子串匹配
    if s1 in s2 or s2 in s1:
        return 0.8 + (0.2 * min(len(s1), len(s2)) / max(len(s1), len(s2)))
    
    # Levenshtein距离匹配
    def levenshtein_distance(text1, text2):
        if len(text1) < len(text2):
            return levenshtein_distance(text2, text1)
        if len(text2) == 0:
            return len(text1)
        previous_row = range(len(text2) + 1)
        for i, c1 in enumerate(text1):
            current_row = [i + 1]
            for j, c2 in enumerate(text2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 0.0
    similarity = 1.0 - (distance / max_len)
    return similarity

def find_song_by_keyword(keyword: str, min_similarity: float = 0.75):
    """根据关键词查找歌曲

    Args:
        keyword: 关键词
        min_similarity: 最小相似度

    Returns:
        歌曲列表，每个元素为(song, title, title_similarity, alias_similarity, max_similarity)
    """
    keyword_lower = keyword.lower().strip()
    results = []
    seen_songs = set()

    if keyword_lower.isdigit():
        chart_id = int(keyword_lower)
        for song in song_manager.get_all_songs():
            for chart in song.charts:
                if chart.id == chart_id and song.id not in seen_songs:
                    results.append((song, song.title, 1.0, 0.0, 1.0))
                    seen_songs.add(song.id)
        return results

    for song in song_manager.get_all_songs():
        title_similarity = calculate_similarity(keyword_lower, song.title)

        alias_similarity = 0.0
        for alias in song.alias:
            sim = calculate_similarity(keyword_lower, alias)
            if sim > alias_similarity:
                alias_similarity = sim

        max_similarity = max(title_similarity, alias_similarity)

        if max_similarity >= min_similarity:
            results.append((song, song.title, title_similarity, alias_similarity, max_similarity))

    results.sort(key=lambda x: x[4], reverse=True)

    unique_results = []
    seen_songs = set()
    for song, title, title_sim, alias_sim, max_sim in results:
        if song.id not in seen_songs:
            seen_songs.add(song.id)
            unique_results.append((song, title, title_sim, alias_sim, max_sim))

    return unique_results

async def check_blacklist(event: Event) -> bool:
    if isinstance(event, GroupMessageEvent):
        return not group_blacklist.is_blocked(event.group_id)
    return True
bind_token = on_command("bind", aliases={"绑定"}, priority=5, block=True, rule=check_blacklist)

@bind_token.handle()
async def handle_bind_token(event: Event, args: Message = CommandArg()):
    user_id = event.user_id
    arg_text = args.extract_plain_text().strip()
    print(f"[DEBUG] bind called with arg_text: {arg_text[:20]}...")
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    parts = arg_text.split() if arg_text else []
    if parts and parts[0].lower() == "help":
        help_msg = "绑定命令帮助\n\n"
        help_msg += "使用方法: /bind <Import-Token>\n\n"
        help_msg += "说明:\n"
        help_msg += "1. 请在水鱼查分器官网生成 Import-Token\n"
        help_msg += "2. 登录水鱼查分器: https://www.diving-fish.com/maimaidx/prober/\n"
        help_msg += "3. 点击 '编辑个人资料'\n"
        help_msg += "4. 找到 '生成 Import-Token' 按钮并点击\n"
        help_msg += "5. 复制生成的 Import-Token\n"
        help_msg += "6. 使用 /bind <Import-Token> 命令绑定账号\n\n"
        help_msg += "示例:\n"
        help_msg += "/bind 1234567890abcdef1234567890abcdef\n"
        await bind_token.finish(help_msg)
    
    if not arg_text:
        await bind_token.finish(
            "Usage: bind <Import-Token>\n"
            "请在水鱼查分器官网生成 Import-Token:\n"
            "https://www.diving-fish.com/maimaidx/prober/\n"
            "登录后 -> 编辑个人资料 -> 生成 Import-Token\n"
            "使用 /bind help 查看详细帮助"
        )
    
    import_token = arg_text.split()[0]
    print(f"[DEBUG] import_token: {import_token[:20]}...")
    
    client = get_diving_fish_client()
    print(f"[DEBUG] client: {client}")
    if not client:
        await bind_token.finish("水鱼查分器服务未配置，请联系管理员")
    
    player_info = await client.get_player_info_by_token(import_token)
    print(f"[DEBUG] player_info: {player_info}")
    if not player_info:
        await bind_token.finish("验证失败，请检查 Import-Token 是否正确")
    
    user_token_manager.set_token(user_id, player_info.username, import_token)
    await bind_token.finish(f"绑定成功！\n用户名: {player_info.username}\n昵称: {player_info.nickname}\nRating: {player_info.rating}")

unbind_token = on_command("unbind", aliases={"解绑"}, priority=5, block=True, rule=check_blacklist)

@unbind_token.handle()
async def handle_unbind_token(event: Event, args: Message = CommandArg()):
    user_id = event.user_id
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    arg_text = args.extract_plain_text().strip()
    parts = arg_text.split() if arg_text else []
    if parts and parts[0].lower() == "help":
        help_msg = "解绑命令帮助\n\n"
        help_msg += "使用方法: /unbind\n\n"
        help_msg += "说明:\n"
        help_msg += "- 该命令会解除您当前绑定的水鱼账号\n"
        help_msg += "- 解绑后需要重新绑定才能使用查分功能\n\n"
        help_msg += "示例:\n"
        help_msg += "/unbind - 解除当前绑定的水鱼账号\n"
        await unbind_token.finish(help_msg)
    
    if user_token_manager.remove_token(user_id):
        await unbind_token.finish("已解除水鱼账号绑定")
    else:
        await unbind_token.finish("您还没有绑定水鱼账号")

check_score = on_command("score", aliases={"查分"}, priority=5, block=True, rule=check_blacklist)

@check_score.handle()
async def handle_check_score(event: Event, args: Message = CommandArg()):
    user_id = event.user_id
    
    user_token = user_token_manager.get_token(user_id)
    if not user_token:
        await check_score.finish(
            "您还没有绑定水鱼账号\n"
            "请使用 bind <用户名> <Import-Token> 进行绑定"
        )
    
    client = get_diving_fish_client()
    if not client:
        await check_score.finish("水鱼查分器服务未配置，请联系管理员")
    
    arg_text = args.extract_plain_text().strip()
    
    # 检查是否有 help 参数（只检测紧跟命令的第一个参数）
    parts = arg_text.split() if arg_text else []
    if parts and parts[0].lower() == "help":
        help_msg = "查分命令帮助\n\n"
        help_msg += "使用方法: /score [参数]\n\n"
        help_msg += "参数说明:\n"
        help_msg += "- -id <谱面ID> - 按谱面ID查询\n"
        help_msg += "- -n <歌曲名> - 按歌曲名查询\n"
        help_msg += "- -d <难度> - 指定难度 (basic, advanced, expert, master, remaster)\n"
        help_msg += "- 难度参数: basic/bs/b, advanced/adv/a, expert/exp/e, master/mas/m, remaster/rem/r\n"
        help_msg += "- 类型参数: dx, std\n\n"
        help_msg += "示例:\n"
        help_msg += "/score Yorugao - 查询歌曲 'Yorugao' 的 Master 难度成绩\n"
        help_msg += "/score -id 11307 - 查询谱面ID为 11307 的 Master 难度成绩\n"
        help_msg += "/score -id 11307 -d expert - 查询谱面ID为 11307 的 Expert 难度成绩\n"
        help_msg += "/score -n Yorugao - 查询歌曲 'Yorugao' 的成绩\n"
        await check_score.finish(help_msg)
    
    if not arg_text:
        player_info = await client.get_player_info(user_token.diving_fish_username, user_token.import_token)
        if player_info:
            msg = f"水鱼查分器信息\n\n"
            msg += f"用户名: {player_info.username}\n"
            msg += f"昵称: {player_info.nickname}\n"
            msg += f"Rating: {player_info.rating}\n"
            if player_info.plate:
                msg += f"牌子: {player_info.plate}\n"
            msg += f"\n使用 score <歌曲名> 查询单曲成绩\n"
            msg += f"使用 score -id <谱面id> 查询指定ID的谱面成绩\n"
            msg += f"使用 score -n <歌曲名> 查询指定歌名的成绩\n"
            msg += f"使用 score help 查看详细帮助\n"
            await check_score.finish(msg)
        else:
            await check_score.finish("获取玩家信息失败，请重新绑定")
    
    parts = arg_text.split()
    query_type = "auto"
    query_value = ""
    target_difficulty = "master"
    target_type = "DX"
    
    # 解析参数
    i = 0
    while i < len(parts):
        part = parts[i]
        part_lower = part.lower()
        
        if part == "-n":
            query_type = "name"
            # 取后续所有字符作为歌名
            query_value = " ".join(parts[i+1:])
            break
        elif part == "-id":
            query_type = "id"
            if i + 1 < len(parts):
                query_value = parts[i+1]
                i += 1
        elif part == "-d":
            # 指定难度
            if i + 1 < len(parts):
                difficulty_arg = parts[i+1].lower()
                if difficulty_arg in ["basic", "bs", "b"]:
                    target_difficulty = "basic"
                elif difficulty_arg in ["advanced", "adv", "a"]:
                    target_difficulty = "advanced"
                elif difficulty_arg in ["expert", "exp", "e"]:
                    target_difficulty = "expert"
                elif difficulty_arg in ["master", "mas", "m"]:
                    target_difficulty = "master"
                elif difficulty_arg in ["remaster", "rem", "r"]:
                    target_difficulty = "remaster"
                i += 1
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
            # 自动模式，根据参数类型判断
            if query_type == "auto":
                query_value = arg_text
        i += 1
    
    # 处理自动模式
    if query_type == "auto":
        if query_value.isdigit():
            query_type = "id"
        else:
            query_type = "name"
    
    # 执行查询
    if query_type == "id":
        # 按ID查询
        try:
            chart_id = int(query_value)
            results = find_song_by_keyword(str(chart_id))
            if not results:
                await check_score.finish(f"未找到ID为 {chart_id} 的谱面")
        except ValueError:
            await check_score.finish("请输入有效的谱面ID")
    else:
        # 按歌名查询
        results = find_song_by_keyword(query_value, min_similarity=0.5)
        if not results:
            await check_score.finish(f"未找到匹配的歌曲")

    has_100_title_match = any(r[2] == 1.0 for r in results)

    if len(results) > 1 and not has_100_title_match:
        msg = f"找到 {len(results)} 个匹配结果:\n\n"
        for i, (song, title, title_sim, alias_sim, max_sim) in enumerate(results[:10], 1):
            msg += f"{i}. {title} (ID: {song.id}, 相似度: {max_sim:.2f})\n"
        if len(results) > 10:
            msg += f"... 还有 {len(results) - 10} 个结果"
        await check_score.finish(msg)

    if has_100_title_match:
        song, song_title, _, _, _ = next(r for r in results if r[2] == 1.0)
    else:
        song, song_title, _, _, _ = results[0]
    
    # 根据查询类型和谱面类型来确定target_type
    found_chart = None
    if query_type == "id":
        # 按ID查询时，需要找到匹配ID的谱面的类型
        chart_id = int(query_value)
        for chart in song.charts:
            if chart.id == chart_id:
                found_chart = chart
                break
        if found_chart:
            target_type = "DX" if found_chart.type == SongType.DX else "SD"
        else:
            # 如果没找到匹配的谱面，使用歌曲的默认类型
            target_type = "DX" if song.type == SongType.DX else "SD"
    else:
        # 按歌名查询时，使用歌曲的类型
        target_type = "DX" if song.type == SongType.DX else "SD"
    
    # 根据查询类型获取谱面ID
    if query_type == "id":
        chart_id = int(query_value)
    else:
        # 按歌名查询时，无法确定谱面ID，使用第一个谱面的ID
        chart_id = song.charts[0].id if song.charts else None
        if chart_id is None:
            await check_score.finish("该歌曲没有可查询的谱面")
    
    print(f"[DEBUG] 调用 get_song_score_by_id: username={user_token.diving_fish_username}, chart_id={chart_id}, difficulty={target_difficulty}")
    score = await client.get_song_score_by_id(
        user_token.diving_fish_username,
        chart_id,
        target_difficulty,
        user_token.import_token,
        song_manager
    )
    print(f"[DEBUG] get_song_score_by_id 返回: {score}")
    
    if not score:
        await check_score.finish(f"未找到歌曲 '{song_title}' 的成绩记录")
    
    msg = f"成绩查询结果\n\n"
    msg += f"歌曲: {score.title}\n"
    msg += f"类型: {score.type}\n"
    msg += f"难度: {DIFFICULTY_NAMES.get(score.level_index, score.level)} {score.level}\n"
    msg += f"达成率: {score.achievement:.4f}%\n"
    msg += f"DX Score: {score.dx_score} / {score.dx_score_max} ({score.dx_rating:.1f}%)\n"
    
    if score.fc:
        fc_names = {"fc": "FC", "fcplus": "FC+", "ap": "AP", "applus": "AP+"}
        msg += f"FC: {fc_names.get(score.fc.lower(), score.fc)}\n"
    
    if score.fs:
        fs_names = {"fs": "FS", "fsplus": "FS+", "fsd": "FSD", "fsdplus": "FSD+"}
        msg += f"FS: {fs_names.get(score.fs.lower(), score.fs)}\n"
    
    if score.rate:
        rate_names = {"d": "D", "c": "C", "b": "B", "bb": "BB", "bbb": "BBB", 
                      "a": "A", "aa": "AA", "aaa": "AAA", "s": "S", "sp": "S+", 
                      "ss": "SS", "ssp": "SS+", "sss": "SSS", "sssp": "SSS+"}
        msg += f"评价: {rate_names.get(score.rate.lower(), score.rate)}\n"
    
    await check_score.finish(msg)