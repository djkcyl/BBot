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
from ....core.group_config import GroupPermission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("添加vip"), "groupid" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, groupid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if groupid.matched:
        say = groupid.result.display
        if say.isdigit():
            gp = GroupPermission(int(say))
            if gp.add_to_vips():
                await app.send_friend_message(friend, MessageChain("成功将群设定为 vip 群"))
            else:
                await app.send_friend_message(friend, MessageChain("该群已是 vip 群"))
        else:
            await app.send_friend_message(friend, MessageChain("群号仅可为数字"))
    else:
        await app.send_friend_message(friend, MessageChain("未输入群号"))
