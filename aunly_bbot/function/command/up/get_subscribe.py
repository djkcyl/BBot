from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At
from graia.ariadne.message.parser.twilight import (
    ElementMatch,
    ElementResult,
    RegexMatch,
    Twilight,
)
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
import time
from ....core import BOT_Status
from ....core.bot_config import BotConfig
from ....core.control import Interval, Permission
from ....core.data import get_sub_by_group
from ....utils.time_tools import calc_time_total

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(["at" @ ElementMatch(At, optional=True), RegexMatch(r"查看(本群)?(订阅|关注)列表")])
        ],
        decorators=[Permission.require(), Interval.require()],
    ),
)
async def sub_list(app: Ariadne, group: Group, at: ElementResult):
    if at.result:
        at_element: At = at.result  # type: ignore
        if at_element.target != BotConfig.Mirai.account:
            return
    sublist = get_sub_by_group(group.id)

    sublist_count = len(sublist)
    if sublist_count == 0:
        await app.send_group_message(group, MessageChain("本群未订阅任何 UP"))
    else:
        msg = [f"本群共订阅 {sublist_count} 个 UP\n注：带*号的表示该 UP 已被设定自定义昵称"]
        for i, sub in enumerate(sublist, 1):
            live_time = BOT_Status.living.get(str(sub.uid), -1)
            if live_time > 100000:
                live = f" 🔴直播中: {calc_time_total(time.time() - live_time)}"
            elif live_time >= 0:
                live = " 🔴直播中"
            else:
                live = ""
            msg.append(f"\n{i}. {f'*{sub.nick}' if sub.nick else sub.uname}（{sub.uid}）{live}")

        await app.send_group_message(group, MessageChain(msg))
