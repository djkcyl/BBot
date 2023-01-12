import sys

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.lifecycle import AccountLaunch
from graiax.playwright.interface import PlaywrightContext
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core.bot_config import BotConfig
from utils.bilibili_request import hc

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[AccountLaunch]))
async def main(app: Ariadne):
    """
    Graia 成功启动
    """
    try:
        logger.info("正在获取浏览器版本")
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

        page = browser_context.context.pages[0]
        version = await page.evaluate("navigator.appVersion")
        logger.info(f"[BiliBili推送] 浏览器启动完成，当前版本 {version}")
        logger.debug(await browser_context.context.cookies())
        await page.close()
    except Exception as e:
        capture_exception(e)
        logger.error(f"[BiliBili推送] 浏览器启动失败 {e}")
        sys.exit(1)

    logger.info("[BiliBili推送] 正在获取首页 Cookie")
    await hc.get("https://bilibili.com/", follow_redirects=True)
    logger.debug(hc.cookies)

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
