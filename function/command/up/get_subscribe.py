from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.exceptions import PropagationCancelled
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

from library import get_group_sublist
from core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(RegexMatch(r"(查看)?(本群)?(订阅|关注)列表"))],
        decorators=[Permission.require(), Interval.require()],
        priority=10,
    )
)
async def sub_list(app: Ariadne, group: Group):

    sublist = get_group_sublist(group.id)
    sublist_count = len(sublist)
    if sublist_count == 0:
        await app.send_group_message(group, MessageChain("本群未订阅任何 UP"))
    else:
        msg = [f"本群共订阅 {sublist_count} 个 UP\n注：带*号的表示该 UP 已被设定自定义昵称"]
        for i, data in enumerate(sublist, 1):
            uid, name, nick = data
            msg.append(f"\n{i}. {f'*{nick}' if nick else name}（{uid}）")
        await app.send_group_message(group, MessageChain(msg))

    raise PropagationCancelled