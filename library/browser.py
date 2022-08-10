from pathlib import Path
from typing import Optional
from playwright.async_api import Browser, async_playwright

from core.bot_config import BotConfig

user_data_dir = Path("data").joinpath("browser")


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
