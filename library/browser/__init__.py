import sys

from pathlib import Path
from loguru import logger
from typing import Optional
from playwright.__main__ import main
from playwright.async_api import Browser, async_playwright

from core.bot_config import BotConfig

user_data_dir = Path(__file__).parent.joinpath("data")


_browser: Optional[Browser] = None


async def init() -> Browser:
    global _browser
    browser = await async_playwright().start()
    _browser = await browser.chromium.launch_persistent_context(
        user_data_dir,
        headless=True,
        device_scale_factor=2 if BotConfig.Bilibili.mobile_style else 1.25,
        user_agent=(
            "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36"
        )
        if BotConfig.Bilibili.mobile_style
        else None,
    )
    if not BotConfig.Bilibili.mobile_style:
        await _browser.add_cookies(
            [{"name": "hit-dyn-v2", "value": "1", "domain": ".bilibili.com", "path": "/"}]
        )

    return _browser


async def get_browser() -> Browser:
    return _browser or await init()


def install():
    """自动安装、更新 Chromium"""

    logger.info("检查 Chromium 更新")
    sys.argv = ["", "install", "chromium"]
    try:
        main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("未知错误，Chromium 下载失败")
            exit()


install()
