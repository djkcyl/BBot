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
from core.group_config import GroupPermission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("添加白名单"), "groupid" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, groupid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if groupid.matched:
        say = groupid.result.asDisplay()
        gp = GroupPermission(say)
        if say.isdigit():
            if gp.add_to_whitelist():
                await app.sendFriendMessage(friend, MessageChain.create("成功将该群加入白名单"))
            else:
                await app.sendFriendMessage(friend, MessageChain.create("该群已在白名单中"))
        else:
            await app.sendFriendMessage(friend, MessageChain.create("群号仅可为数字"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入群号"))
