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

ADD_ERROR_MSG = f"""增加失败, 请正确输入!
请按照 [指令 --name 组名 --uids UID] 格式进行添加

指令: 
(添加|增加)(主播|[uU][pP])到订阅组

参数: 
--name 订阅组名称
--uids up主的uid, 多个uid以空格分割

例:
增加主播到订阅组 --name XXX --uids 123456
添加up到订阅组 --name XXX --uids 123456 234567
"""


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch("^(添加|增加)(主播|[uU][pP])(到订阅组)*"),
                    "groupName" @ ArgumentMatch("--name", optional=True, nargs='*', type=str),
                    "sublist" @ ArgumentMatch("--uids", optional=True, nargs='*', type=int)
                ],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, groupName: RegexResult, sublist: RegexResult):
    """
        通过指定的命令进行添加up主到对应的订阅组中

        Attributes:
            groupName: 要添加的订阅组名称
            sublist: 要添加的订阅列表
    """
    Permission.manual(friend, Permission.MASTER)

    if groupName.matched and sublist.matched:
        group_name = ' '.join(groupName.result) if len(groupName.result) > 1 else groupName.result[0]
        uid_list: list = sublist.result is list  # 已经是list
        if len(uid_list) == 0:
            await app.sendFriendMessage(friend, MessageChain.create(ADD_ERROR_MSG))
            return
        sg = SubGroup(group_name)
        if sg.is_in_groupNames():
            if sg.add_to_subGroups(uid_list):
                await app.sendFriendMessage(friend, MessageChain.create(f"添加到订阅组 [{group_name}] 成功"))
            else:
                await app.sendFriendMessage(friend, MessageChain.create(
                    f"添加失败, 订阅组 [{group_name}] 添加后up主数量将超过12个!"))
        else:
            await app.sendFriendMessage(friend, MessageChain.create("添加的订阅组名称不存在!"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create(ADD_ERROR_MSG))
