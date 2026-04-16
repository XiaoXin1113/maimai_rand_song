from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, Event
from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType

song_manager = SongManager()
song_selector = SongSelector(song_manager)

random_song = on_command("随机选歌", rule=to_me(), priority=5)

@random_song.handle()
async def handle_random_song(bot: Bot, event: Event):
    args = str(event.get_message()).strip().split()
    
    criteria = SelectionCriteria(count=1)
    
    if len(args) > 1:
        try:
            level = float(args[1])
            criteria.min_level = level - 0.5
            criteria.max_level = level + 0.5
        except ValueError:
            pass
    
    result = song_selector.select_random(criteria)
    
    if result.songs:
        song = result.songs[0]
        msg = f"🎵 随机选歌结果\n\n"
        msg += f"歌曲：{song.title}\n"
        msg += f"艺术家：{song.artist}\n"
        msg += f"类型：{song.type}\n"
        if song.genre:
            msg += f"流派：{song.genre}\n"
        if song.difficulties:
            msg += f"难度：{song.difficulties}\n"
        msg += f"\n共找到 {result.total_available} 首符合条件的歌曲"
        await random_song.finish(msg)
    else:
        await random_song.finish("没有找到符合条件的歌曲")

help_cmd = on_command("帮助", rule=to_me(), priority=5)

@help_cmd.handle()
async def handle_help():
    help_text = """🤖 maimai随机选歌机器人

指令列表：
@我 随机选歌 - 随机选择一首歌曲
@我 随机选歌 [等级] - 随机选择指定等级的歌曲
@我 帮助 - 显示此帮助信息

版本：Alpha-0.0.1
"""
    await help_cmd.finish(help_text)
