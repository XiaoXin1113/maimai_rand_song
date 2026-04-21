#!/usr/bin/env python3
"""
测试配置加载脚本
用于验证 settings 配置是否正确加载
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import settings

def test_settings():
    """测试配置加载"""
    print("=" * 50)
    print("配置测试")
    print("=" * 50)
    
    print(f"\nSUPERUSER: {settings.SUPERUSER}")
    print(f"BOT_SUPERUSERS: {settings.BOT_SUPERUSERS}")
    print(f"\nBOT_HOST: {settings.BOT_HOST}")
    print(f"BOT_PORT: {settings.BOT_PORT}")
    print(f"\nWEB_HOST: {settings.WEB_HOST}")
    print(f"WEB_PORT: {settings.WEB_PORT}")
    
    # 测试超级用户验证
    test_user_id = "3299323251"
    is_super = test_user_id in settings.BOT_SUPERUSERS
    print(f"\n测试用户 {test_user_id} 是否为超级用户: {is_super}")
    
    print("\n" + "=" * 50)
    print("配置测试完成")
    print("=" * 50)

if __name__ == "__main__":
    test_settings()