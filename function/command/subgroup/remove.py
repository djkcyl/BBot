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

from core.control import Permission
from core.subgroup_config import SubGroup

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("移除订阅组"), "groupName" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, groupName: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if groupName.matched:
        say = groupName.result.asDisplay()
        sg = SubGroup(say)
        if sg.remove_from_groupNames():
            await app.sendFriendMessage(
                friend, MessageChain.create(f"成功将该名称 [{say}] 移除订阅组")
            )
        else:
            await app.sendFriendMessage(
                friend, MessageChain.create(f"该名称 [{say}] 并不在订阅组中")
            )
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入订阅组名称"))
