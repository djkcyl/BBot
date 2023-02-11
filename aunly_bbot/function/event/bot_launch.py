import sys
import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.lifecycle import AccountLaunch
from graiax.playwright.interface import PlaywrightContext
from graia.saya.builtins.broadcast.schema import ListenerSchema

from ...core.bot_config import BotConfig
from ...utils.bilibili_request import hc
from ...utils.update_version import update_version

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[AccountLaunch]))
async def main(app: Ariadne):
    """
    Graia 成功启动并链接到 Mirai HTTP API 后执行的函数
    """
    if BotConfig.update_check:
        update = await update_version()
        if update:
            old_version, new_version = update
            logger.warning(f"[版本更新] 检测到新版本：{new_version} > {old_version}")
            await app.send_friend_message(
                BotConfig.master, MessageChain(f"检测到新版本：{new_version} > {old_version}")
            )
        else:
            logger.success("[版本更新] 当前版本为最新版本")

    try:
        logger.info("[Playwright] 正在获取浏览器版本")
        browser_context = app.launch_manager.get_interface(PlaywrightContext)
        if not BotConfig.Bilibili.mobile_style:
            await browser_context.context.add_cookies(
                [
                    {
                        "name": "hit-dyn-v2",
                        "value": "1",
                        "domain": ".bilibili.com",
                        "path": "/",
                    }
                ]
            )

        async with browser_context.page() as page:
            version = await page.evaluate("navigator.appVersion")
            logger.info(f"[BiliBili推送] 浏览器启动完成，当前版本 {version}")
            logger.debug(await browser_context.context.cookies())
    except Exception as e:
        capture_exception(e)
        logger.error(f"[BiliBili推送] 浏览器启动失败 {e}")
        sys.exit(1)

    logger.info("[BiliBili推送] 正在获取首页 Cookie")

    for _ in range(3):
        try:
            await hc.get("https://bilibili.com/", follow_redirects=True)
            break
        except Exception as e:
            logger.error(f"[BiliBili推送] 获取首页 Cookie 失败 {e}，正在重试")
            await asyncio.sleep(2)
    else:
        logger.error("[BiliBili推送] 获取首页 Cookie 失败，已达最大重试次数")
        sys.exit(1)

    logger.info("Graia 成功启动")
    group_list = await app.get_group_list()
    group_num = len(group_list)
    master = await app.get_friend(BotConfig.master)
    if not master:
        logger.error(f"当前未添加主人好友（{BotConfig.master}），请手动添加")
        sys.exit(1)
    await app.send_friend_message(
        BotConfig.master,
        MessageChain(
            "BBot-Graia 成功启动。",
            f"\n当前 {BotConfig.name} 共加入了 {group_num} 个群",
        ),
    )

    if BotConfig.Debug.enable:
        debug_msg = []
        for group in BotConfig.Debug.groups:
            debug_group = await app.get_group(group)
            debug_msg.append(
                f"{debug_group.id}（{debug_group.name}）" if debug_group else f"{group}（当前未加入该群）"
            )
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(
                "当前为 Debug 模式，将仅接受\n",
                "\n".join(debug_msg),
                f"\n以及 {master.nickname}（{master.id}） 的消息",
            ),
        )
