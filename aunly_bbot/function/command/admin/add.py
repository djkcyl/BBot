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
from ....core.bot_config import BotConfig

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("添加管理员"), "adminid" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend, adminid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if adminid.matched:
        say = adminid.result.display
        if say.isdigit():
            if int(say) in BotConfig.admins:
                await app.send_friend_message(friend, MessageChain("该账号已是管理员"))
            else:
                BotConfig.admins.append(int(say))
                BotConfig.save()
                await app.send_friend_message(friend, MessageChain("成功将该账号设定为管理员"))
        else:
            await app.send_friend_message(friend, MessageChain("管理员账号仅可为数字"))
    else:
        await app.send_friend_message(friend, MessageChain("未输入管理员账号"))
