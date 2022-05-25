from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

from library import get_group_sublist
from core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(RegexMatch(r"(查看)?(本群)?(订阅|关注)列表"))],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def sub_list(app: Ariadne, group: Group):

    sublist = get_group_sublist(group.id)
    sublist_count = len(sublist)
    if sublist_count == 0:
        await app.sendGroupMessage(group, MessageChain.create("本群未订阅任何 UP"))
    else:
        await app.sendGroupMessage(
            group,
            MessageChain.create(f"本群共订阅 {sublist_count} 个 UP\n", "\n".join(sublist)),
        )
