from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch


from data import get_sub_by_group
from core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(RegexMatch(r"查看(本群)?(订阅|关注)列表"))],
        decorators=[Permission.require(), Interval.require()],
    ),
)
async def sub_list(app: Ariadne, group: Group):
    sublist = get_sub_by_group(group.id)
    sublist_count = len(sublist)
    if sublist_count == 0:
        await app.send_group_message(group, MessageChain("本群未订阅任何 UP"))
    else:
        msg = [f"本群共订阅 {sublist_count} 个 UP\n注：带*号的表示该 UP 已被设定自定义昵称"]
        msg.extend(
            f"\n{i}. {f'*{data.nick}' if data.nick else data.uname}（{data.uid}）"
            for i, data in enumerate(sublist, 1)
        )

        await app.send_group_message(group, MessageChain(msg))
