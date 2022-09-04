import time
import contextlib

from pathlib import Path
from loguru import logger
from playwright.async_api._generated import Request
from playwright._impl._api_types import TimeoutError

from core.bot_config import BotConfig

from .browser import get_browser


error_path = Path("data").joinpath("error")
error_path.mkdir(parents=True, exist_ok=True)


async def get_dynamic_screenshot(id):
    st = int(time.time())
    browser = await get_browser()
    for i in range(3):
        page = await browser.new_page()
        try:
            page.on("requestfinished", network_request)
            page.on("requestfailed", network_requestfailed)
            if BotConfig.Bilibili.mobile_style:
                url = f"https://m.bilibili.com/dynamic/{id}"
                await page.set_viewport_size({"width": 400, "height": 780})
                with contextlib.suppress(TimeoutError):
                    await page.goto(url, wait_until="networkidle", timeout=20000)
                if "bilibili.com/404" in url:
                    logger.warning(f"[Bilibili] {id} 动态不存在，稍后再试")
                    break
                await page.add_script_tag(
                    content=(
                        # 去除打开app按钮
                        "document.getElementsByClassName('launch-app-btn').forEach(v=>v.remove());"
                        # 去除关注按钮
                        "document.getElementsByClassName('dyn-header__following').forEach(v=>v.remove());"
                        # 修复字体与换行问题
                        "const dyn=document.getElementsByClassName('dyn-card')[0];"
                        "dyn.style.fontFamily='Noto Sans CJK SC, sans-serif';"
                        "dyn.style.overflowWrap='break-word'"
                    )
                )
                card = await page.query_selector(".dyn-card")
                assert card
                clip = await card.bounding_box()
                assert clip
            else:
                url = f"https://t.bilibili.com/{id}"
                await page.set_viewport_size({"width": 2560, "height": 1080})
                with contextlib.suppress(TimeoutError):
                    await page.goto(url, wait_until="networkidle", timeout=20000)
                if "bilibili.com/404" in url:
                    logger.warning(f"[Bilibili] {id} 动态不存在，稍后再试")
                    break
                card = await page.query_selector(".card")
                assert card
                clip = await card.bounding_box()
                assert clip
                bar = await page.query_selector(".bili-dyn-action__icon")
                assert bar
                bar_bound = await bar.bounding_box()
                assert bar_bound
                clip["height"] = bar_bound["y"] - clip["y"] - 2
            image = await page.screenshot(clip=clip, full_page=True, type="jpeg", quality=98)
            await page.close()
            return image
        except Exception:
            url = page.url
            if "bilibili.com/404" in url:
                logger.error(f"[Bilibili] {id} 动态不存在，正在重试")
            else:
                logger.exception(f"[BiliBili推送] {id} 动态截图失败，正在重试：")
                await page.screenshot(
                    path=f"{error_path}/{id}_{i}_{st}.jpg",
                    full_page=True,
                    type="jpeg",
                    quality=80,
                )
            with contextlib.suppress():
                await page.close()
    return None


async def network_request(request: Request):
    url = request.url
    method = request.method
    response = await request.response()
    if response:
        status = response.status
        timing = "%.2f" % response.request.timing["responseEnd"]
    else:
        status = "/"
        timing = "/"
    logger.debug(f"[Response] [{method} {status}] {timing}ms <<  {url}")


def network_requestfailed(request: Request):
    url = request.url
    fail = request.failure
    method = request.method
    logger.warning(f"[RequestFailed] [{method} {fail}] << {url}")
