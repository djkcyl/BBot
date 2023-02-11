import asyncio

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from ...core.control import Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/公告"), "anything" @ WildcardMatch()])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def main(app: Ariadne, anything: RegexResult):

    if anything.matched:
        msg = anything.result.display
        sent = []
        for group in await app.get_group_list():
            if group.id in sent:
                continue
            await app.send_group_message(group, MessageChain(f"公告 - {group.id}：\n{msg}"))
            sent.append(group.id)
            await asyncio.sleep(2)
