from pathlib import Path
from typing import Optional
from playwright.async_api import BrowserContext, async_playwright

from core.bot_config import BotConfig

user_data_dir = Path("data").joinpath("browser")


_browser: Optional[BrowserContext] = None


async def init() -> BrowserContext:
    global _browser
    browser = await async_playwright().start()
    chromium = browser.chromium
    _browser = await chromium.launch_persistent_context(
        user_data_dir,
        headless=True,
        device_scale_factor=2 if BotConfig.Bilibili.mobile_style else 1.25,
        user_agent=(
            "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36"
        )
        if BotConfig.Bilibili.mobile_style
        else "",
    )
    if not BotConfig.Bilibili.mobile_style:
        await _browser.add_cookies(
            [{"name": "hit-dyn-v2", "value": "1", "domain": ".bilibili.com", "path": "/"}]
        )

    return _browser


async def get_browser() -> BrowserContext:
    return _browser or await init()
