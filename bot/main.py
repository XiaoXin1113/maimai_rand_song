import nonebot
import os
import sys
from pathlib import Path
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

sys.path.insert(0, str(Path(__file__).parent.parent))

nonebot.init(
    command_start={"", "/", "！"},
    command_sep={".", " "}
)

driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

from core import init_diving_fish_client

diving_fish_token = os.getenv("DIVING_FISH_DEVELOPER_TOKEN", "")
if diving_fish_token:
    init_diving_fish_client(diving_fish_token)
else:
    init_diving_fish_client()

nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()
