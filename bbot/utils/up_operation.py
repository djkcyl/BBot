import asyncio
import contextlib

from typing import Union
from loguru import logger
from bilireq.grpc.dynamic import grpc_get_user_dynamics

from ..core import BOT_Status
from ..core.bot_config import BotConfig
from ..core.group_config import GroupPermission
from ..core.data import (
    add_sub,
    uid_exists,
    get_sub_data,
    set_uid_name,
    uid_in_group,
    get_sub_by_uid,
    get_sub_by_group,
    delete_sub_by_uid,
    unsub_uid_by_group,
)

from .bilibili_request import relation_modify


async def subscribe_uid(uid: Union[str, int], groupid: Union[str, int]):
    """在某个群订阅某个 up"""
    uid = str(uid)
    groupid = str(groupid)
    gp = GroupPermission(int(groupid))
    BOT_Status["init"] = False
    while BOT_Status["dynamic_updating"] and BotConfig.Bilibili.use_login:
        await asyncio.sleep(0.1)

    if not uid:
        BOT_Status["init"] = True
        return "Bot 状态异常，订阅失败，请稍后再试"
    r = await grpc_get_user_dynamics(int(uid))
    if not r:
        BOT_Status["init"] = True
        return f"该 UP（{uid}）状态异常，订阅失败"
    try:
        if len(r.list) == 1:
            dyn = r.list[0]
        elif r.list[0].modules[0].module_author.is_top:
            dyn = r.list[1]
        else:
            dyn = r.list[0]
        up_name = dyn.modules[0].module_author.author.name
    except IndexError:
        BOT_Status["init"] = True
        return f"该 UP（{uid}）未发送任何动态，订阅失败"
    if uid_in_group(uid, groupid):
        BOT_Status["init"] = True
        return f"本群已订阅 UP {up_name}（{uid}），请勿重复订阅"
    if len(get_sub_by_group(groupid)) >= BotConfig.max_subsubscribe and not gp.is_vip():
        BOT_Status["init"] = True
        return f"每个群聊最多仅可订阅 {BotConfig.max_subsubscribe} 个 UP"
    need_sub = not uid_exists(uid)
    add_sub(uid, up_name, groupid)

    if need_sub and BotConfig.Bilibili.use_login:
        resp = await relation_modify(uid, 1)
        if not resp or resp["code"] != 0:
            await unsubscribe_uid(uid, groupid)
            BOT_Status["init"] = True
            return f"UP（{uid}）订阅失败"
        if int(dyn.extend.dyn_id_str) > BOT_Status["offset"] if BOT_Status["offset"] else 0:
            BOT_Status["offset"] = int(dyn.extend.dyn_id_str)
    elif not BotConfig.Bilibili.use_login:
        if BOT_Status["offset"] is None:
            BOT_Status["offset"] = {}
        BOT_Status["offset"][uid] = int(dyn.extend.dyn_id_str)

    if dyn.modules[0].module_author.author.live.live_state == 1:
        BOT_Status["living"][uid] = None
    BOT_Status["init"] = True
    return f"成功在本群订阅 UP {up_name}（{uid}）"


async def unsubscribe_uid(uid, groupid, force=False):
    """在某个群退订某个 up"""
    uid = str(uid)
    groupid = str(groupid)
    logger.info(f"正在群 {groupid} 取消订阅 {uid}")
    while BOT_Status["dynamic_updating"] and not force and BotConfig.Bilibili.use_login:
        await asyncio.sleep(0.1)
    BOT_Status["init"] = False

    if not uid_in_group(uid, groupid):
        BOT_Status["init"] = True
        logger.info(f"群 {groupid} 未订阅 {uid}")
        return f"本群未订阅该 UP（{uid}）"
    up_name = get_sub_data(uid, groupid).uname
    if len(get_sub_by_uid(uid)) == 1:
        await delete_uid(uid)
    else:
        logger.info(f"正在从取消订阅 {uid}")
        unsub_uid_by_group(uid, groupid)
    BOT_Status["init"] = True
    logger.info(f"成功从群 {groupid} 取消订阅 UP {up_name}（{uid}）")
    return f"{up_name}（{uid}）退订成功"


async def delete_uid(uid):
    """直接删除订阅的某个 up"""
    logger.info(f"正在从 BliBili 取消订阅 {uid}")
    uid = str(uid)
    if BotConfig.Bilibili.use_login:
        resp = await relation_modify(uid, 2)
        if resp and resp["code"] == 0:
            logger.info(f"取关 {uid} api 操作成功")
        else:
            logger.error(f"取关 {uid} 失败：{resp}")
            return False
    else:
        BOT_Status["offset"].pop(uid, None)
        with contextlib.suppress(KeyError):
            del BOT_Status["living"][uid]
    if uid_exists(uid):
        delete_sub_by_uid(uid)
    else:
        logger.warning(f"{uid} 不存在于订阅列表中")
    logger.info(f"成功从 BliBili 取消订阅 {uid}")
    return True


def set_name(uid, name):
    uid = str(uid)

    if uid_exists(uid):
        set_uid_name(uid, name)
        return True
    else:
        return False


def set_nick(uid, groupid, nick):
    """设置某个 up 在某个群的昵称"""
    uid = str(uid)
    groupid = str(groupid)

    if uid_in_group(uid, groupid):
        data = get_sub_data(uid, groupid)
        data.nick = nick
        data.save()
        return True
    else:
        return False


def set_atall(uid, groupid, atall):
    """设置某个 up 在某个群的 @全体"""
    uid = str(uid)
    groupid = str(groupid)

    if uid_in_group(uid, groupid):
        data = get_sub_data(uid, groupid)
        data.atall = atall
        data.save()
        return True
    else:
        return False


async def delete_group(groupid) -> list[str]:
    """删除某个群的所有订阅"""
    remove_list = []
    logger.info(f"正在删除群 {groupid} 的所有订阅")
    for data in get_sub_by_group(groupid):
        await unsubscribe_uid(data.uid, data.group, True)
        remove_list.append(data.uid)
    return remove_list
