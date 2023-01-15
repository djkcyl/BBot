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
                [FullMatch("移除订阅组"), "group_name" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, group_name: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if group_name.matched:
        say = group_name.result.display
        sg = SubGroup(say)
        if sg.remove_from_group_names():
            await app.send_friend_message(friend, MessageChain(f"成功将该名称 [{say}] 移除订阅组"))
        else:
            await app.send_friend_message(friend, MessageChain(f"该名称 [{say}] 并不在订阅组中"))
    else:
        await app.send_friend_message(friend, MessageChain("未输入订阅组名称"))
