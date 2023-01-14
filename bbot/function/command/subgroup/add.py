from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from ....core.control import Permission
from ....core.subgroup_config import SubGroup

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("添加订阅组"), "group_name" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, group_name: RegexResult):
    """
    添加订阅组指令

    Attributes:
        group_name: 订阅组名称, 用于添加组
    """
    Permission.manual(friend, Permission.MASTER)
    if group_name.matched:
        say = group_name.result.display
        sg = SubGroup(say)
        if sg.add_to_group_names():
            await app.send_friend_message(friend, MessageChain(f"成功将名称 [{say}] 加入订阅组"))
        else:
            await app.send_friend_message(friend, MessageChain(f"该名称 [{say}] 已在订阅组中"))
    else:
        await app.send_friend_message(friend, MessageChain("未输入订阅组名称"))
