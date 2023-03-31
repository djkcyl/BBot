import json
import httpx

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from .core.control import Permission
from .utils.bilibili_request import grpc_get_playview

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/test")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def main(app: Ariadne, group: Group):
    print(await grpc_get_playview(439357034, 1076145927))
