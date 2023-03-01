import os

from pathlib import Path
from loguru import logger
from fastapi import status
from fastapi import FastAPI
from fastapi.responses import Response
from playwright.async_api import async_playwright
from playwright.async_api._generated import BrowserContext
from graiax.playwright.installer import install_playwright

from ..utils.dynamic_shot import screenshot
from ..utils.fonts_provider import get_font
from ..utils.detect_package import is_package


DYNAMIC_SHOT_CACHE = Path("data", "cache")
DYNAMIC_SHOT_CACHE.mkdir(parents=True, exist_ok=True)
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = (
    "0" if is_package else Path(__file__).parent.parent.joinpath("static", "browser").as_posix()
)
PLAYWRIGIT: BrowserContext = None  # type: ignore
app = FastAPI(title="BBot Playwright API", version="0.1.0")


@app.on_event("startup")
async def init_playwright():
    global PLAYWRIGIT
    logger.info("正在下载字体...")
    await get_font()
    logger.success("字体下载完成！")

    await install_playwright(browser_type="firefox")
    pw = await async_playwright().start()
    ff = await pw.firefox.launch_persistent_context(
        Path("data").joinpath("browser"),
        device_scale_factor=2,
        user_agent=(
            "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36"
        ),
    )
    PLAYWRIGIT = ff
    logger.info("[Playwright] 正在获取浏览器版本")
    page = await PLAYWRIGIT.new_page()
    version = await page.evaluate("navigator.appVersion")
    logger.info(f"[BiliBili推送] 浏览器启动完成，当前版本 {version}")
    logger.debug(await PLAYWRIGIT.cookies())


@app.get("/dynamic/{dynid}")
async def get_up(dynid: str):
    imagefile = DYNAMIC_SHOT_CACHE.joinpath(f"{dynid}.jpg")
    if imagefile.exists():
        logger.info(f"动态 {dynid} 已缓存")
        page_shot = imagefile.read_bytes()
    else:
        page_shot = await screenshot(dynid, PLAYWRIGIT, False)

    if page_shot:
        imagefile.write_bytes(page_shot)
        return Response(page_shot)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
