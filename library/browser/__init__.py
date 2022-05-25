import sys

from pathlib import Path
from loguru import logger
from typing import Optional
from playwright.__main__ import main
from playwright.async_api import Browser, async_playwright


user_data_dir = Path(__file__).parent.joinpath("data")


_browser: Optional[Browser] = None


async def init() -> Browser:
    global _browser
    browser = await async_playwright().start()
    _browser = await browser.chromium.launch_persistent_context(
        user_data_dir,
        headless=True,
        device_scale_factor=1.25,
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
