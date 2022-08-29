import sys

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core.bot_config import BotConfig
from library.browser import get_browser

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def main(app: Ariadne):
    """
    Graia 成功启动
    """
    try:
        logger.info("正在获取浏览器版本")
        browser = await get_browser()
        page = await browser.new_page()
        version = await page.evaluate("() => navigator.appVersion")
        logger.info(f"[BiliBili推送] 浏览器启动完成，当前版本 {version}")
    except Exception as e:
        logger.error("[BiliBili推送] 浏览器启动失败")
        logger.error(e)
        sys.exit(1)

    logger.info("Graia 成功启动")
    groupList = await app.get_group_list()
    groupNum = len(groupList)
    master = await app.get_friend(BotConfig.master)
    if not master:
        logger.error(f"当前未添加主人好友（{BotConfig.master}），请手动添加")
        sys.exit(1)
    await app.send_friend_message(
        BotConfig.master,
        MessageChain(
            "BBot-Graia成功启动。",
            f"\n当前 {BotConfig.name} 共加入了 {groupNum} 个群",
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
