import json
import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core import BOT_Status
from data import get_all_uid
from library import delete_uid
from core.bot_config import BotConfig
from library.grpc import grpc_dynall_get, grpc_uplist_get
from library.bilibili_request import (
    set_token,
    save_token,
    token_refresh,
    bilibili_login,
    relation_modify,
)

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def init(app: Ariadne):

    await asyncio.sleep(1)
    cache, login_data = await bilibili_login()

    logger.info(f"[BiliBili推送] 登录完成，token：{login_data['data']['token_info']}")

    if cache:
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(
                f"[BiliBili推送] 使用缓存登录成功\n{json.dumps(login_data['data']['token_info'], indent=2)}"
            ),
        )

    resp = await token_refresh()
    if resp["code"] == 0:
        set_token(resp)
        save_token()
        logger.success(f"[BiliBili推送] 刷新 token 成功，token：{resp['data']['token_info']}")
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(
                f"[BiliBili推送] 刷新 token 成功\n{json.dumps(resp['data']['token_info'], indent=2)}"
            ),
        )
    else:
        logger.error(f"[BiliBili推送] 刷新 token 失败，{resp}")
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(f"[BiliBili推送] 刷新 token 失败，{resp}"),
        )
        exit()

    # 初始化
    subid_list = get_all_uid()
    resp = await grpc_uplist_get()

    # 检测在数据库但不在B站关注列表的uid
    for up in subid_list:
        for uid in resp.items:
            if up == str(uid.uid):
                break
        else:
            logger.warning(f"[BiliBili推送] {up} 不在关注列表中，正在修复")
            resp = await relation_modify(up, 1)
            if resp["code"] != 0:
                await delete_uid(up)
                logger.error(f"[BiliBili推送] {up} 订阅修复失败，请检查后重启 Bot：{resp}")
                await app.send_friend_message(
                    BotConfig.master,
                    MessageChain(f"[BiliBili推送] UP {up} 订阅修复失败，请检查后重启 Bot：{resp}"),
                )
                exit()
            else:
                logger.info(f"[BiliBili推送] {up} 订阅修复成功")
            await asyncio.sleep(1)

    # 检测在B站关注列表但不在数据库的uid
    if resp.items:
        for uid in resp.items:
            if str(uid.uid) not in subid_list:
                logger.warning(f"[BiliBili推送] {uid.name}（{uid.uid}）在关注列表中，但不在数据库中，正在取消关注")
                resp = await delete_uid(uid.uid)
                if resp["code"] == 0:
                    await app.send_friend_message(
                        BotConfig.master,
                        MessageChain(
                            f"[BiliBili推送] {uid.name}（{uid.uid}）在关注列表中，但不在数据库中，正在取消关注"
                        ),
                    )
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(
                        f"[BiliBili推送] {uid.name}（{uid.uid}）取消关注失败，请检查后重启 Bot：{resp}"
                    )
                    exit()

            # 顺便检测直播状态
            if uid.live_info.status:
                logger.info(f"[BiliBili推送] {uid.name} 已开播")
                BOT_Status["liveing"][str(uid.uid)] = None
    logger.info(f"[BiliBili推送] 直播初始化完成，当前 {len(BOT_Status['liveing'])} 个 UP 正在直播")

    # 动态初始化
    sub_num = len(subid_list)
    if sub_num == 0:
        await asyncio.sleep(1)
        logger.info("[BiliBili推送] 未订阅任何账号，初始化结束")
        BOT_Status["init"] = True
        return
    await asyncio.sleep(1)

    resp = await grpc_dynall_get()
    BOT_Status["offset"] = int(resp[-1].extend.dyn_id_str)
    logger.info(f"[BiliBili推送] 动态初始化完成，offset：{BOT_Status['offset']}")

    logger.info(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控")

    await asyncio.sleep(2)
    BOT_Status["init"] = True

    await app.send_friend_message(
        BotConfig.master,
        MessageChain(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控，初始化完成"),
    )
