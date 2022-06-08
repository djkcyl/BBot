import argparse
import re

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexResult,
    WildcardMatch, RegexMatch, ArgumentMatch, ParamMatch, FullMatch,
)

from core.control import Permission
from core.subgroup_config import SubGroup

channel = Channel.current()

REMOVE_ERROR_MSG = f"""删除失败, 请正确输入!
请按照 [指令 --name 组名 --uid UID] 格式进行添加

指令: 
从订阅组(移除|删除)(主播|[uU][pP])

参数: 
--name 订阅组名称
--uid up主的uid

例:
从订阅组删除主播 --name XXX --uid 123456
从订阅组移除up --name XXX --uid 123456
"""


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch("^(从订阅组)(删除|移除)(主播|[uU][pP])*"),
                    "groupName" @ ArgumentMatch("--name", optional=True, nargs='*', type=str),
                    "uid" @ ArgumentMatch("--uid", optional=True, nargs='*', type=int)
                ],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, groupName: RegexResult, uid: RegexResult):
    Permission.manual(friend, Permission.MASTER)

    if groupName.matched and uid.matched:
        group_name = ' '.join(groupName.result) if len(groupName.result) > 1 else groupName.result[0]
        uid_list: list = uid.result is list  # 已经是list
        if len(uid_list) == 0:
            await app.sendFriendMessage(friend, MessageChain.create(REMOVE_ERROR_MSG))
            return
        sg = SubGroup(group_name)
        if sg.is_in_groupNames():
            uid = uid_list[0]
            if sg.remove_from_subGroup_ups(uid):
                await app.sendFriendMessage(friend, MessageChain.create(f"从 [{group_name}] 订阅组中删除 [uid: {uid}] 成功"))
            else:
                await app.sendFriendMessage(friend, MessageChain.create(
                    f"删除失败, 订阅组 [{group_name}] 中并无订阅的up主!"))
        else:
            await app.sendFriendMessage(friend, MessageChain.create("删除的订阅组名称不存在!"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create(REMOVE_ERROR_MSG))
