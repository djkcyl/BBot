import contextlib

from loguru import logger
from playwright._impl._api_types import TimeoutError

from core.bot_config import BotConfig

from .browser import get_browser


async def get_dynamic_screenshot(id):
    browser = await get_browser()
    for _ in range(3):
        try:
            page = None
            page = await browser.new_page()
            if BotConfig.Bilibili.mobile_style:
                url = f"https://m.bilibili.com/dynamic/{id}"
                await page.set_viewport_size({"width": 400, "height": 780})
                with contextlib.suppress(TimeoutError):
                    await page.goto(url, wait_until="networkidle", timeout=15000)
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
                    '<div class="launch-app-btn dynamic-float-openapp">'
                    '<div class="m-dynamic-float-openapp">'
                    "<span>打开APP，查看更多精彩内容</span></div> <!----></div>",
                    "",
                )
                await page.set_content(content)
                card = await page.query_selector(".dyn-card")
                assert card
                clip = await card.bounding_box()
                assert clip
                image = await page.screenshot(
                    clip=clip, full_page=True, type="jpeg", quality=98
                )
            else:
                url = f"https://t.bilibili.com/{id}"
                await page.set_viewport_size({"width": 2560, "height": 1080})
                with contextlib.suppress(TimeoutError):
                    await page.goto(url, wait_until="networkidle", timeout=10000)
                card = await page.query_selector(".card")
                assert card
                clip = await card.bounding_box()
                assert clip
                bar = await page.query_selector(".text-bar")
                assert bar
                bar_bound = await bar.bounding_box()
                assert bar_bound
                clip["height"] = bar_bound["y"] - clip["y"] - 2

            await page.close()
            return image
        except Exception as e:
            logger.error(f"[BiliBili推送] {id} 动态截图失败，正在重试：")
            logger.exception(e)
    return None
