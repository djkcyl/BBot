import asyncio
import contextlib

from loguru import logger
from datetime import datetime
from graia.saya import Channel
from grpc.aio import AioRpcError
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from graia.ariadne.model import MemberPerm
from graia.ariadne.message.element import AtAll
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.connection.util import UploadMethod
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_seconds
from bilireq.grpc.dynamic import grpc_get_user_dynamics
from bilireq.exceptions import ResponseCodeError, GrpcError
from graia.ariadne.exception import UnknownTarget, AccountMuted, RemoteException
from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import (
    FoldType,
    DynamicItem,
    DynamicType,
    DynModuleType,
)

from ...core import BOT_Status
from ...core.context import Context
from ...core.bot_config import BotConfig
from ...utils.dynamic_shot import get_dynamic_screenshot
from ...utils.up_operation import delete_group, delete_uid, set_name
from ...utils.bilibili_request import (
    get_b23_url,
    dynamic_like,
    grpc_get_dynamic_details,
    grpc_get_followed_dynamics_noads,
)
from ...core.data import (
    uid_exists,
    get_all_uid,
    is_dyn_pushed,
    get_sub_by_uid,
    insert_dynamic_push,
    is_dyn_pushed_in_group,
    insert_dyn_push_to_group,
)

channel = Channel.current()


@channel.use(SchedulerSchema(every_custom_seconds(3)))
async def main(app: Ariadne):

    logger.debug("[Dynamic Pusher] Dynamic Pusher running now...")
    subid_list = get_all_uid()
    sub_sum = len(subid_list)

    if not BOT_Status["init"]:
        logger.debug("[Dynamic Pusher] Dynamic Pusher is not init")
        await asyncio.sleep(3)
        return
    elif sub_sum == 0:
        logger.debug("[Dynamic Pusher] Dynamic Pusher is not have subids")
        await asyncio.sleep(5)
        return

    BOT_Status["dynamic_updating"] = True
    BOT_Status["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 动态更新检测
    # 获取当前登录账号的动态列表
    logger.debug("[Dynamic] Start to get dynamic list")
    if BotConfig.Bilibili.use_login:
        try:
            dynall = await asyncio.wait_for(grpc_get_followed_dynamics_noads(), timeout=10)
        except AioRpcError as e:
            logger.error(f"[Dynamic] Get dynamic list failed: {e.details()}")
            BOT_Status["dynamic_updating"] = False
            return
        except asyncio.TimeoutError:
            logger.debug("[Dynamic] Get dynamic list failed")
            BOT_Status["dynamic_updating"] = False
            return

        # 判断请求是否拿到数据
        logger.debug("[Dynamic] Start to check dynamic")
        if dynall:
            logger.debug(f"[Dynamic] Get {len(dynall)} dynamics")
            new_dyn = [
                x
                for x in dynall
                if int(x.extend.dyn_id_str) > BOT_Status.get("offset", int(x.extend.dyn_id_str))
                and not is_dyn_pushed(int(x.extend.dyn_id_str))
            ]
            logger.debug(f"[Dynamic] {len(new_dyn)} new dynamics")
            # 轮询动态列表
            for dyn in new_dyn:
                try:
                    up_id = str(dyn.modules[0].module_author.author.mid)
                    up_name = dyn.modules[0].module_author.author.name
                    dynid = int(dyn.extend.dyn_id_str)
                    logger.debug(f"[Dynamic] Check dynamic {dynid}, {up_name}({up_id})")
                    try:
                        if dynid <= BOT_Status.get("offset", dynid) or is_dyn_pushed(dynid):
                            continue
                    except ValueError:
                        continue
                    if await push(app, dyn):
                        continue
                except ScreenshotError:
                    return

            # 将当前检测到的第一条动态 id 设置为最新的动态 id
            if BOT_Status["offset"] > int(dynall[-1].extend.dyn_id_str):
                logger.info("[BiliBili推送] 有 UP 删除了动态")

            BOT_Status["offset"] = int(dynall[-1].extend.dyn_id_str)
        else:
            logger.error("[Dynamic] Gotten dynamic is empty")
            logger.error(dynall)

    else:
        # 把uid分组，每组发送一次请求
        check_list = [
            subid_list[i : i + BotConfig.Bilibili.concurrency]
            for i in range(0, sub_sum, BotConfig.Bilibili.concurrency)
        ]
        logger.debug(f"Get {sub_sum} uid, split to {len(check_list)} groups")
        for subid_group in check_list:
            logger.debug(f"Gathering {len(subid_group)} uid: {' '.join(subid_group)}")
            await asyncio.gather(
                *[check_uid(app, uid) for uid in subid_group], return_exceptions=True
            )

    BOT_Status["last_finish"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    BOT_Status["dynamic_updating"] = False
    logger.debug("[Dynamic] Updating finished")
    await asyncio.sleep(0.5)


async def push(app: Ariadne, dyn: DynamicItem):
    """推送动态"""

    up_id = str(dyn.modules[0].module_author.author.mid)
    up_name = dyn.modules[0].module_author.author.name
    dynid = dyn.extend.dyn_id_str
    dyn_desc = " ".join(
        [x.module_desc.text for x in dyn.modules if x.module_type == DynModuleType.module_desc]
    )

    logger.debug(f"[Dynamic] Start to push dynamic {dynid}")

    if uid_exists(up_id):
        logger.info(
            f"[BiliBili推送] {dynid} | {up_name}({up_id}) 更新了动态，共有 {len(get_sub_by_uid(up_id))} 个群订阅了该 UP"
        )
        # 判断折叠动态
        module_type_list = [i.module_type for i in dyn.modules]
        if DynModuleType.module_fold in module_type_list:
            logger.debug(f"[Dynamic] {dynid} | {up_name}({up_id}) is folded")
            fold = dyn.modules[module_type_list.index(DynModuleType.module_fold)]
            if fold.module_fold.fold_type == FoldType.FoldTypeUnite:
                fold_ids = fold.module_fold.fold_ids
                logger.debug(f"[Dynamic] {dynid} | {up_name}({up_id}) fold_ids: {fold_ids}")
                details = await grpc_get_dynamic_details(fold_ids)
                for dynamic in details.list:
                    try:
                        if is_dyn_pushed(dynamic.extend.dyn_id_str):
                            logger.debug(
                                f"[Dynamic] {dynid} | {up_name}({up_id}) is pushed, skip"
                            )
                            continue
                    except ValueError:
                        continue
                    await push(app, dynamic)

        logger.debug(f"[Dynamic] Getting screenshot of {dynid} | {up_name}({up_id})")
        shot_image = await get_dynamic_screenshot(dyn)

        if shot_image:
            logger.debug(f"[Dynamic] Get dynamic screenshot {dynid} | {up_name}({up_id})")
            dyn_img = await app.upload_image(shot_image, UploadMethod.Group)
            logger.debug(f"[Dynamic] Upload dynamic screenshot {dynid} | {up_name}({up_id})")
        else:
            logger.debug(
                f"[Dynamic] Get dynamic screenshot {dynid} | {up_name}({up_id}) failed"
            )
            err_msg = f"[BiliBili推送] {dynid} | {up_name}({up_id}) 更新了动态，截图失败"
            logger.error(err_msg)
            await app.send_friend_message(BotConfig.master, MessageChain(err_msg))
            BOT_Status["dynamic_updating"] = False
            logger.debug("[Dynamic] Stop updating")
            raise ScreenshotError()

        if set_name(up_id, up_name):
            logger.debug(f"[Dynamic] Set {up_id} name to {up_name}")
        else:
            logger.debug(f"[Dynamic] Can't set {up_id} name to {up_name}")

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

        if BotConfig.Event.push:
            await app.send_friend_message(
                BotConfig.master,
                MessageChain(
                    f"UP {up_name}（{up_id}）{type_text}\n",
                    dyn_img,
                    "\n",
                    await get_b23_url(f"https://t.bilibili.com/{dynid}"),
                ),
            )

        for data in get_sub_by_uid(up_id):
            if BotConfig.Debug.enable and int(data.group) not in BotConfig.Debug.groups:
                continue
            if data.dynamic:
                nick = f"*{up_nick} " if (up_nick := data.nick) else f"UP {up_name}（{up_id}）"
                msg = [
                    f"{nick}{type_text}\n",
                    dyn_img,
                    "\n",
                    await get_b23_url(f"https://t.bilibili.com/{dynid}"),
                ]
                if data.atall:
                    bot_perm = (await app.get_group(int(data.group))).account_perm

                    if bot_perm in [
                        MemberPerm.Administrator,
                        MemberPerm.Owner,
                    ]:
                        msg = [AtAll(), " "] + msg
                    else:
                        msg = ["@全体成员 "] + msg
                        msg.append(f"\n\n注：{BotConfig.name} 没有权限@全体成员")
                try:
                    if is_dyn_pushed_in_group(dynid, data.group):
                        logger.debug(
                            f"[Dynamic] {dynid} | {up_name}({up_id}) is pushed in group {data.group}, skip"
                        )
                        continue
                    logger.debug(
                        f"[Dynamic] Send dynamic {dynid} | {up_name}({up_id}) to {data.group}"
                    )
                    Context.push_type.set("dynamic")
                    Context.push_id.set(dynid)
                    await app.send_group_message(
                        int(data.group),
                        MessageChain(msg),
                    )
                    insert_dyn_push_to_group(dynid, data.group)
                    await asyncio.sleep(2)
                except UnknownTarget:
                    logger.warning(
                        f"[BiliBili推送] {dynid} | {up_name}({up_id}) 推送失败，找不到该群 {data.group}，正在取消订阅"
                    )
                    delete = await delete_group(data.group)
                    logger.warning(f"[BiliBili推送] 已删除群 {data.group} 订阅的 {len(delete)} 个 UP")
                    with contextlib.suppress(UnknownTarget):
                        await app.quit_group(int(data.group))
                except AccountMuted:
                    group = await app.get_group(int(data.group))
                    group = f"{group.name}（{group.id}）" if group else data.group
                    logger.warning(
                        f"[BiliBili推送] {dynid} | {up_name}({up_id}) 推送失败，账号在 {group} 被禁言"
                    )
                except RemoteException as e:
                    if "resultType=46" in str(e):
                        logger.error(
                            f"[BiliBili推送] {dynid} | {up_name}({up_id}) 推送失败，Bot 被限制发送群聊消息"
                        )
                        await app.send_friend_message(
                            BotConfig.master,
                            MessageChain("Bot 被限制发送群聊消息（46 代码），请尽快处理后发送 /init 重新开启推送进程"),
                        )
                        BOT_Status["dynamic_updating"] = True
                        BOT_Status["init"] = False
                        raise ExecutionStop() from e
                    elif "resultType=110" in str(e):  # 110: 可能为群被封
                        logger.warning(
                            f"[BiliBili推送] {dynid} | {up_name}({up_id}) 推送失败，Bot 因未知原因被移出群聊"
                        )
                        delete = await delete_group(data.group)
                        logger.warning(f"[BiliBili推送] 已删除群 {data.group} 订阅的 {len(delete)} 个 UP")
                        with contextlib.suppress(UnknownTarget):
                            await app.quit_group(int(data.group))
                    elif "reason=AT_ALL_LIMITED" in str(e):
                        logger.warning(
                            f"[BiliBili推送] {dynid} | {up_name}({up_id}) 推送失败，Bot 在该群 @全体成员 次数已达上限"
                        )
                        await app.send_group_message(int(data.group), MessageChain(msg[1:]))
                        await asyncio.sleep(1)
                    else:
                        capture_exception()
                        logger.exception(f"[BiliBili推送] {dynid} | {up_name}({up_id}) 推送失败，未知错误")
                except Exception:  # noqa
                    capture_exception()
                    logger.exception(f"[BiliBili推送] {dynid} | {up_name}({up_id}) 推送失败，未知错误")
        if BotConfig.Bilibili.use_login:
            try:
                await dynamic_like(dynid)
                logger.info(f"[BiliBili推送] {dynid} | {up_name}({up_id}) 动态点赞成功")
            except ResponseCodeError as e:
                logger.error(f"[BiliBili推送] {dynid} | {up_name}({up_id}) 动态点赞失败：{e}")
        insert_dynamic_push(
            up_id,
            up_name,
            dynid,
            dyn.card_type,
            dyn_desc,
            len(get_sub_by_uid(up_id)),
        )
    else:
        logger.warning(
            f"[BiliBili推送] {dynid} | {up_name}({up_id}) 没有找到订阅 UP {up_name}（{up_id}）的群，已退订！"
        )
        await delete_uid(up_id)


async def check_uid(app: Ariadne, uid):
    try:
        resp = await asyncio.wait_for(grpc_get_user_dynamics(int(uid)), timeout=10)
    except asyncio.TimeoutError:
        logger.warning(f"[BiliBili推送] {uid} 获取动态超时！")
        return
    except GrpcError as e:
        logger.error(f"[BiliBili推送] {uid} 获取动态失败：[{e.code}] {e.msg}")
        return
    except Exception as e:  # noqa
        capture_exception(e)
        raise e
    if resp:
        resp = [
            x
            for x in resp.list
            if int(x.extend.dyn_id_str)
            > BOT_Status["offset"].get(uid, int(x.extend.dyn_id_str))
        ]
        resp.reverse()
        for dyn in resp:
            if dyn.modules[0].module_author.is_top:
                continue
            try:
                up_id = str(dyn.modules[0].module_author.author.mid)
                up_name = dyn.modules[0].module_author.author.name
                dynid = int(dyn.extend.dyn_id_str)
                logger.debug(f"[Dynamic] Check dynamic {dynid} | {up_name}({up_id})")
                try:
                    if (
                        dynid <= BOT_Status["offset"][up_id]
                        # or up_id in BOT_Status["skip_uid"]
                        or is_dyn_pushed(dynid)
                    ):
                        return
                except ValueError:
                    BOT_Status["offset"][up_id] = dynid
                    return
                await push(app, dyn)

                BOT_Status["offset"][up_id] = dynid

            except ScreenshotError:
                return


class ScreenshotError(Exception):
    pass


@channel.use(SchedulerSchema(every_custom_seconds(2)))
async def debug():
    logger.debug(BOT_Status)
