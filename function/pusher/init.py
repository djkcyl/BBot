import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core import BOT_Status
from library import delete_uid, get_subid_list
from core.bot_config import BotConfig
from library.bilibili_request import bilibili_login, relation_modify
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
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(
                f"[BiliBili推送] 使用缓存登录成功\n账号：{login_data['username']}\nmid：{login_data['data']['token_info']['mid']}"
            ),
        )

    subid_list = get_subid_list()
    # 直播状态初始化
    resp = await grpc_uplist_get()

    for up in subid_list.keys():
        for uid in resp.items:
            if up == str(uid.uid):
                break
        else:
            logger.warning(f"[Init] {up} is not in Bilibili sublist, fixing...")
            resp = await relation_modify(up, 1)
            if resp["code"] != 0:
                await delete_uid(up)
                logger.error(f"订阅失败：{resp['code']}, {resp['message']}")
                exit()

    for uid in resp.items:
        if str(uid.uid) not in subid_list:
            await delete_uid(up)
            logger.error(f"[Init] {uid.name} is not in subidlist json")
            exit()

        if uid.live_info.status:
            logger.info(f"[BiliBili推送] {uid.name} 已开播")
            BOT_Status["liveing"].append(str(uid.uid))
    logger.info(f"[BiliBili推送] 直播初始化完成，当前 {len(BOT_Status['liveing'])} 个 UP 正在直播")

    # 动态初始化
    resp = await grpc_dynall_get()
    BOT_Status["offset"] = int(resp[-1].extend.dyn_id_str)
    logger.info(f"[BiliBili推送] 动态初始化完成，offset：{BOT_Status['offset']}")

    sub_num = len(subid_list)
    if sub_num == 0:
        await asyncio.sleep(1)
        logger.info("[BiliBili推送] 未订阅任何账号，初始化结束")
        BOT_Status["init"] = True
        return
    await asyncio.sleep(1)
    logger.info(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控")

    await asyncio.sleep(2)
    BOT_Status["init"] = True

    await app.send_friend_message(
        BotConfig.master,
        MessageChain(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控，初始化完成"),
    )