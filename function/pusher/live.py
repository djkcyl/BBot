from graia.ariadne.connection.util import UploadMethod
import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, AtAll
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_seconds
from graia.ariadne.model import MemberPerm

from core import BOT_Status
from data import insert_live_push
from core.bot_config import BotConfig
from library.grpc import grpc_uplist_get
from library import get_group_sublist, get_subid_list, set_name, unsubscribe_uid
from library.bilibili_request import get_status_info_by_uids, relation_modify

channel = Channel.current()


@channel.use(SchedulerSchema(every_custom_seconds(3)))
async def main(app: Ariadne):

    if not BOT_Status["init"] or BOT_Status["init"] and len(get_subid_list()) == 0:
        return
    sub_list = get_subid_list().copy()

    # 直播状态更新检测
    try:
        live_statu = await asyncio.wait_for(grpc_uplist_get(), timeout=10)
    except asyncio.TimeoutError:
        logger.debug("[Live] Get live status failed")
    # 由于叔叔的 api 太烂了，会把同一个 up 开播和未开播的状态放在同一个列表里，所以这里需要去重
    # 不过好消息是，这个列表可以按照开播和未开播的顺序排列
    lives = []
    try:
        live_list = live_statu.items
    except Exception:
        return

    _live = [str(up.uid) for up in live_list]
    for up in BOT_Status["liveing"]:
        if up not in _live:
            BOT_Status["liveing"].remove(up)

    for up in live_list:
        up_id = str(up.uid)
        up_name = up.name
        # 检测订阅配置里是否有该 up
        if up_id in sub_list:
            set_name(up_id, up_name)
            if up_id in lives:
                continue
            lives.append(up_id)
            if up_id in BOT_Status["skip_uid"]:
                continue
            # 如果存在直播信息则为已开播
            if up.live_info.status:
                if up_id in BOT_Status["liveing"]:
                    continue
                room_id = up.live_info.room_id
                resp = await get_status_info_by_uids({"uids": [up_id]})
                title = resp["data"][up_id]["title"]
                area_parent = resp["data"][up_id]["area_v2_parent_name"]
                area = resp["data"][up_id]["area_v2_name"]
                room_area = f"{area_parent} / {area}"
                cover_from_user = resp["data"][up_id]["cover_from_user"]
                cover_img = await app.upload_image(
                    await Image(url=cover_from_user).get_bytes(), UploadMethod.Group
                )
                logger.info(f"[BiliBili推送] {up_name} 开播了 - {room_area} - {title}")

                for groupid, data in sub_list[up_id].items():
                    if BotConfig.Debug.enable and groupid not in BotConfig.Debug.groups:
                        continue
                    if data["send"]["live"]:
                        nick = (
                            f"*{up_nick} "
                            if (up_nick := data["nick"])
                            else f"UP {up_name}（{up_id}）"
                        )
                        msg = [
                            f"本群订阅的 {nick}在 {room_area} 区开播啦 ！\n标题：{title}\n",
                            cover_img,
                            f"\nhttps://live.bilibili.com/{room_id}",
                        ]
                        if data["atall"]:
                            bot_perm = (await app.get_group(int(groupid))).account_perm
                            if bot_perm in [
                                MemberPerm.Administrator,
                                MemberPerm.Owner,
                            ]:
                                msg = [AtAll(), " "] + msg
                            else:
                                msg = ["@全体成员 "] + msg
                        try:
                            await app.send_group_message(
                                groupid,
                                MessageChain(msg),
                            )
                            await asyncio.sleep(1)
                        except UnknownTarget:
                            remove_list = []
                            for subid, _, _ in get_group_sublist(groupid):
                                await unsubscribe_uid(subid, groupid)
                                remove_list.append(subid)
                            logger.info(
                                f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个 UP"
                            )

                BOT_Status["liveing"].append(up_id)
                insert_live_push(
                    up_id, True, len(sub_list[up_id]), title, area_parent, area
                )
            elif up_id in BOT_Status["liveing"]:
                BOT_Status["liveing"].remove(up_id)
                logger.info(f"[BiliBili推送] {up_name} 已下播")
                for groupid, data in sub_list[up_id].items():
                    if BotConfig.Debug.enable and groupid not in BotConfig.Debug.groups:
                        continue
                    if data["send"]["live"]:
                        try:
                            nick = (
                                f"{up_nick} "
                                if (up_nick := data["nick"])
                                else f"UP {up_name}（{up_id}）"
                            )
                            await app.send_group_message(
                                groupid,
                                MessageChain(f"本群订阅的 {nick}已下播！"),
                            )

                        except UnknownTarget:
                            remove_list = []
                            for subid, _, _ in get_group_sublist(groupid):
                                await unsubscribe_uid(subid, groupid)
                                remove_list.append(subid)
                            logger.info(
                                f"[BiliBili推送] 发送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个 UP"
                            )
                        await asyncio.sleep(1)
                insert_live_push(up_id, False, len(sub_list[up_id]))
        else:
            logger.warning(f"[BiliBili推送] 未找到订阅 UP {up_name}（{up_id}）的群，已退订！")
            resp = await relation_modify(up_id, 2)
            if resp["code"] == 0:
                logger.info(f"[BiliBili推送] {up_name}（{up_id}）退订成功！")
                await app.send_friend_message(
                    BotConfig.master,
                    MessageChain(
                        f"[BiliBili推送] 未找到订阅 {up_name}（{up_id}）的群，已被退订！",
                    ),
                )
            else:
                logger.error(f"[BiliBili推送] {up_name}（{up_id}）退订失败：{resp}")
