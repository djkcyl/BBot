import random

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from ...core import BOT_Status
from ...core.control import Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("/init")],
            )
        ],
    )
)
async def main(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    if BOT_Status["init"]:
        await app.send_friend_message(friend, MessageChain("已初始化，无需重复操作"))
    else:
        group = random.choice(await app.get_group_list())
        try:
            await app.recall_message(await app.send_group_message(group, MessageChain("test")))
            BOT_Status["init"] = True
            await app.send_friend_message(friend, MessageChain("初始化成功"))
        except RemoteException as e:
            await app.send_friend_message(friend, MessageChain(f"初始化失败，{e}"))
