import pytest
from core import SongManager, SongSelector, SelectionCriteria, Song, Difficulty, SongType

def test_song_creation():
    song = Song(
        id="test001",
        title="测试歌曲",
        artist="测试艺术家",
        type=SongType.STANDARD,
        difficulties={Difficulty.EASY: 1.0, Difficulty.BASIC: 3.0}
    )
    assert song.id == "test001"
    assert song.title == "测试歌曲"
    assert song.type == SongType.STANDARD

def test_selection_criteria():
    criteria = SelectionCriteria(
        min_level=10.0,
        max_level=13.0,
        difficulty=Difficulty.MASTER,
        count=3
    )
    assert criteria.min_level == 10.0
    assert criteria.max_level == 13.0
    assert criteria.difficulty == Difficulty.MASTER
    assert criteria.count == 3

def test_song_selector():
    manager = SongManager()
    selector = SongSelector(manager)
    
    criteria = SelectionCriteria(count=1)
    result = selector.select_random(criteria)
    
    assert result.criteria == criteria
    assert result.total_available >= 0
