import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MemberPerm
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, AtAll
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_seconds

from core import BOT_Status
from core.bot_config import BotConfig
from library.grpc import grpc_dynall_get
from library.text2image import text2image
from library.bilibili_request import relation_modify
from library.dynamic_shot import get_dynamic_screenshot
from library import get_subid_list, get_group_sublist, set_name, unsubscribe_uid
from library.grpc.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicType

channel = Channel.current()


@channel.use(SchedulerSchema(every_custom_seconds(2)))
async def main(app: Ariadne):

    if not BOT_Status["init"]:
        return
    elif len(get_subid_list()) == 0:
        return

    sub_list = get_subid_list().copy()

    # 动态更新检测
    # 获取当前登录账号的动态列表
    dynall = await grpc_dynall_get()
    if not dynall:
        return
    for dyn in dynall:
        try:
            if int(dyn.extend.dyn_id_str) <= BOT_Status["offset"]:
                continue
            elif not BOT_Status["offset"]:
                break
        except ValueError:
            continue
        up_id = str(dyn.modules[0].module_author.author.mid)
        up_name = dyn.modules[0].module_author.author.name
        up_last_dynid = dyn.extend.dyn_id_str
        logger.info(f"[BiliBili推送] {up_name} 更新了动态 {up_last_dynid}")
        try:
            shot_image = await get_dynamic_screenshot(up_last_dynid)
        except Exception as e:
            logger.error(f"[BiliBili推送] {up_name} 更新了动态 {up_last_dynid}，截图失败 {e}")
            error_img = await text2image(f"{up_name} 更新了动态 {up_last_dynid}，截图失败 {e}")
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create(
                    f"[BiliBili推送] {up_name}（{up_id}）的新动态 {up_last_dynid} 截图失败\n",
                    Image(data_bytes=error_img),
                ),
            )
            break
        if up_id in sub_list:
            set_name(up_id, up_name)

            if dyn.card_type == DynamicType.forward:
                type_text = "转发了一条动态！"
            elif dyn.card_type == DynamicType.word:
                type_text = "发布了一条文字动态！"
            elif dyn.card_type == DynamicType.draw:
                type_text = "发布了一条图文动态！"
            elif dyn.card_type == DynamicType.article:
                type_text = "发布了一条专栏！"
            elif dyn.card_type == DynamicType.av:
                type_text = "发布了一条新视频！"
            else:
                type_text = "发布了一条动态！"

            for groupid, data in sub_list[up_id].items():
                if BotConfig.Debug.enable and groupid not in BotConfig.Debug.groups:
                    continue
                if data["send"]["dynamic"]:
                    nick = (
                        f"{up_nick} "
                        if (up_nick := data["nick"])
                        else f"{up_name}（{up_id}）"
                    )
                    msg = [
                        f"本群订阅的 UP {nick}{type_text}",
                        Image(data_bytes=shot_image),
                        f"https://t.bilibili.com/{up_last_dynid}",
                    ]
                    if data["atall"]:
                        bot_perm = (await app.getGroup(int(groupid))).accountPerm

                        if bot_perm in [
                            MemberPerm.Administrator,
                            MemberPerm.Owner,
                        ]:
                            msg = [AtAll(), " "] + msg
                        else:
                            msg = ["@全体成员 "] + msg
                    try:
                        await app.sendGroupMessage(
                            groupid,
                            MessageChain.create(msg),
                        )
                        await asyncio.sleep(1)
                    except UnknownTarget:
                        remove_list = []
                        for subid, _, _ in get_group_sublist(groupid):
                            await unsubscribe_uid(subid, groupid)
                            remove_list.append(subid)
                        logger.warning(
                            f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个 UP"
                        )
                    except Exception as e:
                        logger.error(f"[BiliBili推送] 推送失败，未知错误 \n{type(e)}\n{e}")

        else:
            logger.warning(f"[BiliBili推送] 没有找到订阅 UP {up_name}（{up_id}）的群，已退订！")
            resp = await relation_modify(up_id, 2)
            if resp["code"] == 0:
                logger.info("[BiliBili推送] 退订成功！")
                msg = "已被退订！"
            else:
                logger.error(f"[BiliBili推送] 退订失败：{resp}")
                msg = f"退订失败：{resp}"
            await app.sendFriendMessage(
                BotConfig.master,
                MessageChain.create(
                    f"[BiliBili推送] 未找到订阅 {up_name}（{up_id}）的群，{msg}",
                ),
            )

    # 将当前检测到的第一条动态 id 设置为最新的动态 id
    if BOT_Status["offset"] > int(dynall[-1].extend.dyn_id_str):
        logger.info("[BiliBili推送] 有 UP 删除了动态")
    BOT_Status["offset"] = int(dynall[-1].extend.dyn_id_str)
