import json

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from core import BOT_Status
from core.control import Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(FullMatch("/status"))],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def main(app: Ariadne, group: Group):
    await app.send_group_message(
        group, MessageChain(json.dumps(BOT_Status, indent=2, ensure_ascii=False))
    )