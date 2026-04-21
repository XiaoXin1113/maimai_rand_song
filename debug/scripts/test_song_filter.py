#!/usr/bin/env python3
"""
测试歌曲筛选功能
用于验证歌曲筛选逻辑是否正确
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core import SongManager, SongSelector, SelectionCriteria, Difficulty, SongType

def test_utage_filtering():
    """测试宴会场歌曲筛选"""
    print("=" * 50)
    print("宴会场筛选测试")
    print("=" * 50)
    
    manager = SongManager()
    selector = SongSelector(manager)
    
    # 测试非宴会场筛选
    print("\n1. 测试非宴会场筛选 (utage_only=False):")
    criteria = SelectionCriteria(count=1, utage_only=False)
    result = selector.select_random(criteria)
    print(f"   可选歌曲数量: {result.total_available}")
    
    if result.songs:
        song = result.songs[0]
        print(f"   选中歌曲: {song.title}")
        print(f"   歌曲类型: {song.type}")
        has_utage = any(c.type == SongType.UTAGE for c in song.charts)
        print(f"   是否包含宴会场谱面: {has_utage}")
    
    # 测试宴会场筛选
    print("\n2. 测试宴会场筛选 (utage_only=True):")
    criteria = SelectionCriteria(count=1, utage_only=True)
    result = selector.select_random(criteria)
    print(f"   可选歌曲数量: {result.total_available}")
    
    if result.songs:
        song = result.songs[0]
        print(f"   选中歌曲: {song.title}")
        has_utage = any(c.type == SongType.UTAGE for c in song.charts)
        print(f"   是否包含宴会场谱面: {has_utage}")
    
    print("\n" + "=" * 50)
    print("宴会场筛选测试完成")
    print("=" * 50)

def test_level_filtering():
    """测试等级筛选"""
    print("\n" + "=" * 50)
    print("等级筛选测试")
    print("=" * 50)
    
    manager = SongManager()
    selector = SongSelector(manager)
    
    # 测试等级范围筛选
    print("\n1. 测试等级 12-13 筛选:")
    criteria = SelectionCriteria(min_level=12.0, max_level=13.0, count=1)
    result = selector.select_random(criteria)
    print(f"   可选歌曲数量: {result.total_available}")
    
    print("\n" + "=" * 50)
    print("等级筛选测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_utage_filtering()
    test_level_filtering()