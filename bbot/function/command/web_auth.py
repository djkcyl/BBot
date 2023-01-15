from datetime import timedelta
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Member, Group
from graia.ariadne.message.element import At, Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.amnesia.builtins.memcache import Memcache
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from ...core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/auth"), "anything" @ WildcardMatch()])],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def main(
    app: Ariadne, group: Group, member: Member, source: Source, anything: RegexResult
):

    if anything.matched and (key := anything.result):

        memcache = app.launch_manager.get_interface(Memcache)
        if await memcache.has(key.display):
            if not await memcache.get(key.display):
                await memcache.set(key.display, str(member.id), timedelta(seconds=120))
                await app.send_group_message(
                    group, MessageChain(At(member), " 认证成功"), quote=source
                )
        else:
            await app.send_group_message(group, MessageChain(At(member), " 认证失败"), quote=source)
