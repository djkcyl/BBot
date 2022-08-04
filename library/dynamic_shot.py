import time
import contextlib

from pathlib import Path
from loguru import logger
from playwright.async_api._generated import Request
from playwright._impl._api_types import TimeoutError

from core.bot_config import BotConfig

from .browser import get_browser


error_path = Path("error")
error_path.mkdir(exist_ok=True)


async def get_dynamic_screenshot(id):
    st = int(time.time())
    browser = await get_browser()
    page = await browser.new_page()
    for i in range(3):
        try:
            page.on("requestfinished", network_request)
            page.on("requestfailed", network_requestfailed)
            if BotConfig.Bilibili.mobile_style:
                url = f"https://m.bilibili.com/dynamic/{id}"
                await page.set_viewport_size({"width": 400, "height": 780})
                with contextlib.suppress(TimeoutError):
                    await page.goto(url, wait_until="networkidle", timeout=20000)
                content = await page.content()
                content = content.replace(
                    '<div class="dyn-header__right">'
                    '<div data-pos="follow" class="dyn-header__following">'
                    '<span class="dyn-header__following__icon"></span>'
                    '<span class="dyn-header__following__text">关注</span></div></div>',
                    "",
                )
                content = content.replace(
                    '<div class="dyn-card">',
                    '<div class="dyn-card" '
                    'style="font-family: sans-serif; overflow-wrap: break-word;">',
                )
                content = content.replace(
                    '<div class="launch-app-btn dynamic-float-openapp dynamic-float-btn">'
                    '<div class="m-dynamic-float-openapp">'
                    "<span>打开APP，查看更多精彩内容</span></div> <!----></div>",
                    "",
                )
                await page.set_content(content)
                card = await page.query_selector(".dyn-card")
                assert card
                clip = await card.bounding_box()
                assert clip
            else:
                url = f"https://t.bilibili.com/{id}"
                await page.set_viewport_size({"width": 2560, "height": 1080})
                with contextlib.suppress(TimeoutError):
                    await page.goto(url, wait_until="networkidle", timeout=20000)
                card = await page.query_selector(".card")
                assert card
                clip = await card.bounding_box()
                assert clip
                bar = await page.query_selector(".text-bar")
                assert bar
                bar_bound = await bar.bounding_box()
                assert bar_bound
                clip["height"] = bar_bound["y"] - clip["y"] - 2
            image = await page.screenshot(
                clip=clip, full_page=True, type="jpeg", quality=98
            )
            await page.close()
            return image
        except Exception as e:
            url = page.url
            if "bilibili.com/404" in url:
                logger.error(f"[Bilibili] {id} 动态不存在，正在重试")
            else:
                logger.error(f"[BiliBili推送] {id} 动态截图失败，正在重试：")
                logger.exception(e)
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
