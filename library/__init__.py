import asyncio
import json

from pathlib import Path

from core import BOT_Status

from .grpc import grpc_dyn_get
from .bilibili_request import relation_modify


class SubList:
    subscription_list_json = Path("data/subscription_list.json")

    def __init__(self) -> None:
        if self.subscription_list_json.exists():
            with self.subscription_list_json.open("r") as f:
                self.subscription_list = json.load(f)["subscription"]
        else:
            with self.subscription_list_json.open("w") as f:
                self.subscription_list = {}
                json.dump({"subscription": {}}, f, indent=2)

    def get_data(self):
        return self.subscription_list

    def save(self, data=None):
        if data:
            self.subscription_list_json.write_text(
                json.dumps({"subscription": data}, indent=2, ensure_ascii=False)
            )
        else:
            self.subscription_list_json.write_text(
                json.dumps(
                    {"subscription": self.subscription_list}, indent=2, ensure_ascii=False
                )
            )


sub = SubList()


def get_group_sublist(groupid):
    """获取某个群订阅的 up 列表"""
    return [
        (subuid, data[str(groupid)]["name"], data[str(groupid)]["nick"])
        for subuid, data in sub.get_data().items()
        if str(groupid) in data
    ]


def get_subid_list():
    """获取所有的订阅列表"""
    return sub.get_data()


async def subscribe_uid(uid, groupid) -> str:
    """在某个群订阅某个 up"""
    uid = str(uid)
    groupid = str(groupid)
    # 做一些小处理，用来避免出现奇怪的bug
    while BOT_Status["updateing"]:
        await asyncio.sleep(0.1)
    BOT_Status["init"] = False
    BOT_Status["skip_uid"].append(uid)

    r = await grpc_dyn_get(uid)
    if not r:
        BOT_Status["init"] = True
        return f"该 UP（{uid}）状态异常，订阅失败"
    up_name = r["list"][0]["modules"][0]["module_author"]["author"]["name"]
    uid_sub_group = sub.get_data().get(uid, {})
    if groupid in uid_sub_group:
        BOT_Status["init"] = True
        return f"本群已订阅 UP {up_name}（{uid}），请勿重复订阅"
    if len(get_group_sublist(groupid)) >= 12:
        BOT_Status["init"] = True
        return "每个群聊最多仅可订阅 12 个 UP"
    if uid not in sub.get_data():
        need_sub = True
        sub.get_data()[uid] = {}
    else:
        need_sub = False
    sub.get_data()[uid][groupid] = {
        "name": up_name,
        "nick": None,
        "atall": False,
        "send": {"dynamic": True, "live": True},
    }
    sub.save()
    if need_sub:
        resp = await relation_modify(uid, 1)
        if resp["code"] != 0:
            await unsubscribe_uid(uid, groupid)
            BOT_Status["init"] = True
            return f"订阅失败：{resp['code']}, {resp['message']}"

    BOT_Status["init"] = True

    return f"成功在本群订阅 UP {up_name}（{uid}）"


async def unsubscribe_uid(uid, groupid):
    """在某个群退订某个 up"""
    uid = str(uid)
    groupid = str(groupid)
    while BOT_Status["updateing"]:
        await asyncio.sleep(0.1)
    BOT_Status["init"] = False
    BOT_Status["skip_uid"].append(uid)

    uid_sub_group = sub.get_data().get(uid, {})
    if groupid not in uid_sub_group:
        BOT_Status["init"] = True
        return f"本群未订阅该 UP（{uid}）"
    up_name = uid_sub_group[groupid]["name"]
    up_nick = uid_sub_group[groupid]["nick"]
    if not len(sub.get_data()[uid]) - 1:
        await delete_uid(uid)
    else:
        del sub.get_data()[uid][groupid]
    sub.save()
    BOT_Status["init"] = True
    return f"{up_nick or up_name}（{uid}）退订成功"


async def delete_uid(uid):
    """直接删除订阅的某个 up"""
    uid = str(uid)

    await relation_modify(uid, 2)
    del sub.get_data()[uid]
    sub.save()


def set_name(uid, name):
    uid = str(uid)

    if sub.get_data()[uid]:
        for group in sub.get_data()[uid].keys():
            sub.get_data()[uid][group]["name"] = name
        sub.save()
        return True
    else:
        return False


def set_nick(uid, groupid, nick):
    """设置某个 up 在某个群的昵称"""
    uid = str(uid)
    groupid = str(groupid)

    if sub.get_data()[uid].get(groupid):
        sub.get_data()[uid][groupid]["nick"] = nick or None
        sub.save()
        return True
    else:
        return False


def set_atall(uid, groupid, atall):
    """设置某个 up 在某个群的 @全体"""
    uid = str(uid)
    groupid = str(groupid)

    if sub.get_data()[uid].get(groupid):
        sub.get_data()[uid][groupid]["atall"] = atall
        sub.save()
        return True
    else:
        return False
