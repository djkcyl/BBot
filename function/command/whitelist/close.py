from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from core.control import Permission
from core.bot_config import open_access_control

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("关闭白名单")],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    msg = "白名单关闭成功" if open_access_control() else "白名单当前已关闭"
    await app.send_friend_message(friend, MessageChain(msg))