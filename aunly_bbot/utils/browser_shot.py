import re
import time
import asyncio
import contextlib

from yarl import URL
from pathlib import Path
from loguru import logger
from graia.ariadne import Ariadne
from sentry_sdk import capture_exception
from playwright._impl._api_types import TimeoutError
from graiax.playwright.interface import PlaywrightContext
from playwright.async_api._generated import Request, Page, BrowserContext, Route

from ..core.bot_config import BotConfig

from .fonts_provider import get_font


error_path = Path("data").joinpath("error")
error_path.mkdir(parents=True, exist_ok=True)
mobile_style_js = Path(__file__).parent.parent.joinpath("static", "mobile_style.js")
font_mime_map = {
    "collection": "font/collection",
    "otf": "font/otf",
    "sfnt": "font/sfnt",
    "ttf": "font/ttf",
    "woff": "font/woff",
    "woff2": "font/woff2",
}


async def fill_font(route: Route, request: Request):
    url = URL(request.url)
    if not url.is_absolute():
        raise ValueError("字体地址不合法")
    try:
        logger.debug(f"Font {url.name} requested")
        await route.fulfill(
            path=await get_font(url.query["name"]),
            content_type=font_mime_map.get(url.suffix, None),
        )
        return
    except Exception:
        logger.debug(f"can't get font {url.name}")
        await route.fallback()


async def browser_dynamic(dynid: str):
    app = Ariadne.current()
    browser_context = app.launch_manager.get_interface(PlaywrightContext).context
    return await screenshot(dynid, browser_context)


async def screenshot(dynid: str, browser_context: BrowserContext, log=True):
    logger.info(f"正在截图动态：{dynid}")
    st = int(time.time())
    for i in range(3):
        page = await browser_context.new_page()
        await page.route(re.compile("^https://fonts.bbot/(.+)$"), fill_font)
        try:
            if log:
                page.on("requestfinished", network_request)
            page.on("requestfailed", network_requestfailed)
            if BotConfig.Bilibili.mobile_style:
                page, clip = await get_mobile_screenshot(page, dynid)
            else:
                page, clip = await get_pc_screenshot(page, dynid)
            return await page.screenshot(clip=clip, full_page=True, type="jpeg", quality=98)
        except Notfound:
            logger.error(f"[Bilibili推送] {dynid} 动态不存在")
        except AssertionError:
            logger.exception(f"[BiliBili推送] {dynid} 动态截图失败，正在重试：")
            await page.screenshot(
                path=f"{error_path}/{dynid}_{i}_{st}.jpg",
                full_page=True,
                type="jpeg",
                quality=80,
            )
        except Exception as e:  # noqa
            if "bilibili.com/404" in page.url:
                logger.error(f"[Bilibili推送] {dynid} 动态不存在")
                break
            elif "waiting until" in str(e):
                logger.error(f"[BiliBili推送] {dynid} 动态截图超时，正在重试：")
            else:
                capture_exception()
                logger.exception(f"[BiliBili推送] {dynid} 动态截图失败，正在重试：")
                await page.screenshot(
                    path=f"{error_path}/{dynid}_{i}_{st}.jpg",
                    full_page=True,
                    type="jpeg",
                    quality=80,
                )
        finally:
            with contextlib.suppress():
                await page.close()


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


async def get_mobile_screenshot(page: Page, dynid: str):
    url = f"https://m.bilibili.com/dynamic/{dynid}"

    await page.set_viewport_size({"width": 460, "height": 720})

    with contextlib.suppress(TimeoutError):
        await page.goto(url, wait_until="networkidle", timeout=20000)

    if "bilibili.com/404" in page.url:
        logger.warning(f"[Bilibili推送] {dynid} 动态不存在")
        raise Notfound

    await page.add_script_tag(path=mobile_style_js)
    await page.wait_for_function("getMobileStyle()")

    await page.evaluate(
        f"setFont('{BotConfig.Bilibili.dynamic_font}', '{BotConfig.Bilibili.dynamic_font_source}')"
    )

    # 判断字体是否加载完成
    await page.wait_for_timeout(
        200 if BotConfig.Bilibili.dynamic_font_source == "remote" else 50
    )
    need_wait = ["imageComplete", "fontsLoaded"]
    await asyncio.gather(*[page.wait_for_function(f"{i}()") for i in need_wait])

    card = await page.query_selector(".opus-modules" if "opus" in page.url else ".dyn-card")
    assert card
    clip = await card.bounding_box()
    assert clip
    logger.debug(f"loaded: {clip}")
    return page, clip


async def get_pc_screenshot(page: Page, dynid: str):
    url = f"https://t.bilibili.com/{dynid}"

    await page.set_viewport_size({"width": 2560, "height": 1080})
    with contextlib.suppress(TimeoutError):
        await page.goto(url, wait_until="networkidle", timeout=20000)

    if "bilibili.com/404" in page.url:
        logger.warning(f"[Bilibili推送] {dynid} 动态不存在")
        raise Notfound

    card = await page.query_selector(".card")
    assert card
    clip = await card.bounding_box()
    assert clip
    bar = await page.query_selector(".bili-dyn-action__icon")
    assert bar
    bar_bound = await bar.bounding_box()
    assert bar_bound
    clip["height"] = bar_bound["y"] - clip["y"] - 2
    logger.debug(f"loaded: {clip}")
    return page, clip


class Notfound(Exception):
    pass
