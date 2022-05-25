import json
import asyncio

from pathlib import Path

from core import BOT_Status
from library.bilibili_request import relation_modify
from library.grpc import grpc_dyn_get, grpc_dynall_get


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
    r = await grpc_dyn_get(uid)
    if not r:
        return f"该 UP（{uid}）状态异常，订阅失败"
    up_name = r["list"][0]["modules"][0]["module_author"]["author"]["name"]
    uid_sub_group = sub.get_data().get(uid, {})
    if str(groupid) in uid_sub_group:
        return f"本群已订阅 UP {up_name}（{uid}），请勿重复订阅"
    if len(get_group_sublist(groupid)) >= 12:
        return "每个群聊最多仅可订阅 12 个 UP"
    need_sub = uid not in sub.get_data()
    sub.get_data().get(uid, {})[str(groupid)] = {
        "name": up_name,
        "nick": None,
        "atall": False,
        "send": {"dynamic": True, "live": True},
    }
    sub.save()
    for _ in range(5):
        if dynall := await grpc_dynall_get():
            BOT_Status["offset"] = int(dynall[-1].extend.dyn_id_str)
            break
        else:
            await asyncio.sleep(0.5)
            continue
    if need_sub:
        resp = await relation_modify(uid, 1)
        if resp["code"] == 0:
            sub.get_data()[uid] = {}
        else:
            return f"订阅失败 {resp['message']}"
    return f"成功在本群订阅 UP {up_name}（{uid}）"


async def unsubscribe_uid(uid, groupid):
    """在某个群退订某个 up"""
    uid_sub_group = sub.get_data().get(uid, {})
    if str(groupid) not in uid_sub_group:
        return f"本群未订阅该 UP（{uid}）"
    up_name = uid_sub_group[str(groupid)]["name"]
    up_nick = uid_sub_group[str(groupid)]["nick"]
    sub_copy = sub.get_data().copy()[uid][str(groupid)]
    del sub_copy[uid][str(groupid)]
    if not sub_copy[uid]:
        await delete_uid(uid)
    del sub.get_data()[uid][str(groupid)]
    sub.save()
    for _ in range(5):
        if dynall := await grpc_dynall_get():
            BOT_Status["offset"] = int(dynall[-1].extend.dyn_id_str)
            break
        else:
            await asyncio.sleep(0.5)
            BOT_Status["offset"] = 0
            continue
    return f"{up_nick or up_name}（{uid}）退订成功"


async def delete_uid(uid):
    """直接删除订阅的某个 up"""
    await relation_modify(uid, 2)
    del sub.get_data()[uid]
    sub.save()


def set_name(uid, name):
    if sub.get_data()[uid]:
        for group in sub.get_data()[uid].keys():
            sub.get_data()[uid][group]["name"] = name
        sub.save()
        return True
    else:
        return False


def set_nick(uid, group, nick):
    """设置某个 up 在某个群的昵称"""
    if sub.get_data()[uid].get(str(group)):
        sub.get_data()[uid][str(group)]["nick"] = nick or None
        sub.save()
        return True
    else:
        return False


def set_atall(uid, group, atall):
    """设置某个 up 在某个群的 @全体"""
    if sub.get_data()[uid].get(str(group)):
        sub.get_data()[uid][str(group)]["atall"] = atall
        sub.save()
        return True
    else:
        return False
