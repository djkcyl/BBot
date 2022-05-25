import json

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


def get_group_subsum(groupid):
    """获取某个群订阅的合计"""
    return sum(groupid in sub.get_data()[subuid] for subuid in sub.get_data())


def get_group_sublist(groupid):
    """获取某个群订阅的 up 列表"""
    return [subuid for subuid in sub.get_data() if groupid in sub.get_data()[subuid]]


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
    if get_group_subsum(str(groupid)) == 12:
        return "每个群聊最多仅可订阅 12 个 UP"
    if uid not in sub.get_data():
        resp = await relation_modify(uid, 1)
        if resp["code"] == 0:
            sub.get_data()[uid] = {}
        else:
            return f"订阅失败 {resp['message']}"
    sub.get_data()[uid][str(groupid)] = {
        "nick": None,
        "atall": False,
        "send": {"dynamic": True, "live": True},
    }
    sub.save()
    dynall = await grpc_dynall_get()
    BOT_Status["offset"] = int(dynall[-1].extend.dyn_id_str)
    return f"成功在本群订阅 UP {up_name}（{uid}）"


async def unsubscribe_uid(uid, groupid):
    """在某个群退订某个 up"""
    uid_sub_group = sub.get_data().get(uid, {})
    if str(groupid) not in uid_sub_group:
        return f"本群未订阅该 UP（{uid}）"
    del sub.get_data()[uid][str(groupid)]
    if not sub.get_data()[uid]:
        await delete_uid(uid)
    sub.save()
    dynall = await grpc_dynall_get()
    BOT_Status["offset"] = int(dynall[-1].extend.dyn_id_str)
    return f"退订成功（{uid}）"


async def delete_uid(uid):
    """直接删除订阅的某个 up"""
    await relation_modify(uid, 2)
    del sub.get_data()[uid]
    dynall = await grpc_dynall_get()
    BOT_Status["offset"] = int(dynall[-1].extend.dyn_id_str)
    sub.save()


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
