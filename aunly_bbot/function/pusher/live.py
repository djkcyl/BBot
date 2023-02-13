import time
import asyncio

from loguru import logger
from graia.saya import Channel
from json import JSONDecodeError
from httpx import TransportError
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from graia.ariadne.model import MemberPerm
from bilireq.live import get_rooms_info_by_uids
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.connection.util import UploadMethod
from graia.ariadne.message.element import Image, AtAll
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_seconds
from graia.ariadne.exception import UnknownTarget, AccountMuted, RemoteException

from ...core import BOT_Status
from ...core.bot_config import BotConfig
from ...utils.time_tools import calc_time_total
from ...utils.bilibili_request import get_b23_url
from ...utils.up_operation import delete_group, delete_uid, set_name
from ...core.data import insert_live_push, get_all_uid, get_sub_by_uid, update_cover_by_id

channel = Channel.current()


@channel.use(SchedulerSchema(every_custom_seconds(3)))
async def main(app: Ariadne):
    if not BOT_Status["init"] or BOT_Status["init"] and len(get_all_uid()) == 0:
        await asyncio.sleep(5)
        return
    sub_list = get_all_uid()

    BOT_Status["live_updating"] = True

    for up in BOT_Status["living"].copy():
        if up not in sub_list:
            del BOT_Status["living"][up]
    try:
        try:
            status_infos = await get_rooms_info_by_uids(sub_list)
        except (TransportError, JSONDecodeError) as error:
            logger.warning(f"获取直播间状态失败: {type(error)} {error}")
            await asyncio.sleep(5)
            BOT_Status["live_updating"] = False
            return
        except RuntimeError as error:
            if "The connection pool was closed while" not in str(error):
                raise error
            BOT_Status["live_updating"] = False
            return
    except Exception:  # noqa
        capture_exception()
        logger.exception("获取直播间状态失败:")
        await asyncio.sleep(30)
        BOT_Status["live_updating"] = False
        return
    if status_infos:
        for up, live_data in status_infos.items():
            up_id = up
            up_name = live_data["uname"]
            # 检测订阅配置里是否有该 up
            if up_id in sub_list:
                # if up_id in BOT_Status["skip_uid"]:
                #     continue
                # 如果存在直播信息则为已开播
                logger.debug(
                    f"[Live] {up_name}({up_id}) live_status: {live_data['live_status']}"
                )
                if live_data["live_status"] == 1:
                    # 判断是否在正在直播列表中
                    if up_id in BOT_Status["living"]:
                        continue
                    logger.debug(f"[Live] {up} live_data: {live_data}")
                    BOT_Status["living"][up_id] = live_data["live_time"]  # 设定开播时间
                    # 获取直播信息
                    room_id = live_data["room_id"]
                    title = live_data["title"]
                    area_parent = live_data["area_v2_parent_name"]
                    area = live_data["area_v2_name"]
                    room_area = f"{area_parent} / {area}"
                    cover_img_url = update_cover_by_id(
                        up_id, live_data.get("cover_from_user", live_data.get("keyframe"))
                    )
                    cover_img = (
                        await app.upload_image(
                            await Image(url=cover_img_url).get_bytes(),
                            UploadMethod.Group,
                        )
                        if cover_img_url
                        else None
                    )
                    set_name(up_id, up_name)
                    logger.info(f"[BiliBili推送] {up_name} 开播了 - {room_area} - {title}")

                    # 发送推送消息
                    for data in get_sub_by_uid(up_id):
                        if (  # 判断是否处于 DEBUG 模式
                            BotConfig.Debug.enable
                            and int(data.group) not in BotConfig.Debug.groups
                        ):
                            continue
                        if data.live:  # 判断该群是否开启直播推送
                            group = await app.get_group(int(data.group))
                            nick = (
                                f"*{up_nick} "
                                if (up_nick := data.nick)
                                else f"UP {up_name}（{up_id}）"
                            )
                            msg = [
                                f"{nick}在 {room_area} 区开播啦 ！\n标题：{title}\n",
                                cover_img,
                                "\n" if cover_img else "",
                                await get_b23_url(f"https://live.bilibili.com/{room_id}"),
                            ]

                            if data.atall:  # 判断是否开启@全体推送
                                bot_perm = group.account_perm if group else MemberPerm.Member
                                if bot_perm in [
                                    MemberPerm.Administrator,
                                    MemberPerm.Owner,
                                ]:
                                    msg = [AtAll(), " "] + msg
                                else:
                                    msg = ["@全体成员 "] + msg
                            try:
                                await app.send_group_message(
                                    int(data.group),
                                    MessageChain(msg),
                                )
                                await asyncio.sleep(1)
                            except UnknownTarget:
                                delete = await delete_group(data.group)
                                logger.info(
                                    f"[BiliBili推送] 推送失败，找不到该群 {data.group}，已删除该群订阅的 {len(delete)} 个 UP"
                                )
                            except AccountMuted:
                                group = f"{group.name}（{group.id}）" if group else data.group
                                logger.warning(f"[BiliBili推送] 推送失败，账号在 {group} 被禁言")

                    insert_live_push(
                        up_id, True, len(get_sub_by_uid(up_id)), title, area_parent, area
                    )
                elif up_id in BOT_Status["living"]:
                    logger.debug(f"[Live] {up} live_data: {live_data}")
                    live_time = (
                        "，本次直播时长 "
                        + calc_time_total(time.time() - BOT_Status["living"][up_id])
                        + "。"
                        if BOT_Status["living"][up_id]
                        else "。"
                    )
                    del BOT_Status["living"][up_id]
                    set_name(up_id, up_name)
                    logger.info(f"[BiliBili推送] {up_name} 已下播{live_time}")
                    for data in get_sub_by_uid(up_id):
                        if (
                            BotConfig.Debug.enable
                            and int(data.group) not in BotConfig.Debug.groups
                        ):
                            continue
                        if data.live:
                            try:
                                nick = (
                                    f"*{up_nick} "
                                    if (up_nick := data.nick)
                                    else f"UP {up_name}（{up_id}）"
                                )
                                await app.send_group_message(
                                    int(data.group),
                                    MessageChain(f"{nick}已下播{live_time}"),
                                )
                            except UnknownTarget:
                                delete = await delete_group(data.group)
                                logger.info(
                                    f"[BiliBili推送] 推送失败，找不到该群 {data.group}，已删除该群订阅的 {len(delete)} 个 UP"
                                )
                            except AccountMuted:
                                group = await app.get_group(int(data.group))
                                group = f"{group.name}（{group.id}）" if group else data.group
                                logger.warning(f"[BiliBili推送] 推送失败，账号在 {group} 被禁言")
                            except RemoteException as e:
                                if "resultType=46" in str(e):
                                    logger.error("[BiliBili推送] 推送失败，Bot 被限制发送群聊消息")
                                    await app.send_friend_message(
                                        BotConfig.master,
                                        MessageChain(
                                            "Bot 被限制发送群聊消息（46 代码），请尽快处理后发送 /init 重新开启推送进程"
                                        ),
                                    )
                                    BOT_Status["dynamic_updating"] = True
                                    BOT_Status["init"] = False
                                    raise ExecutionStop() from e
                                else:
                                    capture_exception()
                                    logger.exception("[BiliBili推送] 推送失败，未知错误")
                            except Exception:  # noqa
                                capture_exception()
                                logger.exception("[BiliBili推送] 推送失败，未知错误")
                            await asyncio.sleep(1)
                    insert_live_push(up_id, False, len(get_sub_by_uid(up_id)))
            else:
                logger.warning(f"[BiliBili推送] 未找到订阅 UP {up_name}（{up_id}）的群，正在退订！")
                await delete_uid(up_id)

    BOT_Status["live_updating"] = False
