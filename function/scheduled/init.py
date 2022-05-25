import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core import BOT_Status
from library import get_subid_list
from core.bot_config import BotConfig
from library.bilibili_request import bilibili_login
from library.grpc import grpc_dynall_get, grpc_uplist_get


channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def init(app: Ariadne):

    await asyncio.sleep(1)
    cache, login_data = await bilibili_login()

    logger.info(
        f"[BiliBili推送] 登录完成，账号：{login_data['username']}，mid：{login_data['data']['token_info']['mid']}"
    )

    if cache:
        await app.sendFriendMessage(
            BotConfig.master,
            MessageChain.create(
                f"[BiliBili推送] 使用缓存登录成功\n账号：{login_data['username']}\nmid：{login_data['data']['token_info']['mid']}"
            ),
        )

    subid_list = get_subid_list()
    sub_num = len(subid_list)
    if sub_num == 0:
        await asyncio.sleep(1)
        logger.info("[BiliBili推送] 由于未订阅任何账号，本次初始化结束")
        return
    await asyncio.sleep(1)
    logger.info(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控")

    # 直播状态初始化
    resp = await grpc_uplist_get()
    for uid in resp["items"]:
        if "live_info" in uid:
            logger.info(f"[BiliBili推送] {uid['name']} 已开播")
            BOT_Status["liveing"].append(uid["uid"])

    # 动态初始化
    resp = await grpc_dynall_get()
    BOT_Status["offset"] = int(resp[-1].extend.dyn_id_str)
    logger.info(f"[BiliBili推送] 动态初始化完成，offset：{BOT_Status['offset']}")

    await asyncio.sleep(2)
    BOT_Status["init"] = True

    await app.sendFriendMessage(
        BotConfig.master,
        MessageChain.create(
            f"[BiliBili推送] 将对 {sub_num} 个账号进行监控，当前最后一条动态id为 {BOT_Status['offset']}，初始化完成"
        ),
    )
