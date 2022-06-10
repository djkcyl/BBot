from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
    RegexResult,
)

from library import set_atall
from core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    "act" @ RegexMatch(r"开启|关闭"),
                    RegexMatch(r"@?全体(成员)?"),
                    "uid" @ RegexMatch(r"\d+", optional=True),
                ]
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def main(app: Ariadne, group: Group, act: RegexResult, uid: RegexResult):
    if uid.matched:
        uids = uid.result.display
        if uids.isdigit():
            acts = act.result.display
            if acts == "开启":
                msg = "开启成功" if set_atall(uids, group.id, True) else "该群未关注此 UP"
            elif acts == "关闭":
                msg = "关闭成功" if set_atall(uids, group.id, False) else "该群未关注此 UP"
        else:
            msg = "请输入正确的 UID"
    else:
        msg = "请输入正确的 UID"

    await app.send_group_message(group, MessageChain(msg))