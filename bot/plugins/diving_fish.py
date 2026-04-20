import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message, Event, MessageSegment
from nonebot.params import CommandArg
from core import get_diving_fish_client, SongManager, Difficulty, SongType
from core.user_tokens import user_token_manager
from core.group_blacklist import group_blacklist

song_manager = SongManager()

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

def find_song_by_keyword(keyword: str):
    keyword_lower = keyword.lower().strip()
    
    if keyword_lower.isdigit():
        song_id = int(keyword_lower)
        for song in song_manager.get_all_songs():
            if song.id == song_id:
                return song, song.title
        return None, None
    
    for song in song_manager.get_all_songs():
        if keyword_lower == song.title.lower():
            return song, song.title
        if keyword_lower in song.title.lower():
            return song, song.title
        for alias in song.alias:
            if keyword_lower == alias.lower():
                return song, song.title
            if keyword_lower in alias.lower():
                return song, song.title
    
    return None, None

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
    
    if not arg_text:
        await bind_token.finish(
            "Usage: bind <Import-Token>\n"
            "请在水鱼查分器官网生成 Import-Token:\n"
            "https://www.diving-fish.com/maimaidx/prober/\n"
            "登录后 -> 编辑个人资料 -> 生成 Import-Token"
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
async def handle_unbind_token(event: Event):
    user_id = event.user_id
    
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
    
    if not arg_text:
        player_info = await client.get_player_info(user_token.diving_fish_username, user_token.import_token)
        if player_info:
            msg = f"水鱼查分器信息\n\n"
            msg += f"用户名: {player_info.username}\n"
            msg += f"昵称: {player_info.nickname}\n"
            msg += f"Rating: {player_info.rating}\n"
            if player_info.plate:
                msg += f"牌子: {player_info.plate}\n"
            msg += f"\n使用 score <歌曲名> 查询单曲成绩"
            await check_score.finish(msg)
        else:
            await check_score.finish("获取玩家信息失败，请重新绑定")
    
    keyword = arg_text
    target_difficulty = "master"
    target_type = "DX"
    
    parts = keyword.split()
    for part in parts:
        part_lower = part.lower()
        if part_lower in ["basic", "bs", "b"]:
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
    
    song_keyword = keyword
    for part in parts:
        part_lower = part.lower()
        if part_lower in ["basic", "bs", "b", "advanced", "adv", "a", "expert", "exp", "e", 
                          "master", "mas", "m", "remaster", "rem", "r", "dx", "std"]:
            song_keyword = song_keyword.replace(part, "").strip()
    
    song, song_title = find_song_by_keyword(song_keyword)
    if not song:
        await check_score.finish(f"未找到歌曲 \"{song_keyword}\"")
    
    if song.type == SongType.DX:
        target_type = "DX"
    else:
        target_type = "SD"
    
    score = await client.get_song_score_by_name(
        user_token.diving_fish_username,
        song_title,
        target_difficulty,
        target_type,
        user_token.import_token
    )
    
    if not score:
        await check_score.finish(f"未找到歌曲 \"{song_title}\" 的成绩记录")
    
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
