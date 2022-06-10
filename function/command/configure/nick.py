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
    WildcardMatch,
)

from library import set_nick
from core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    "act" @ RegexMatch(r"设定|删除"),
                    RegexMatch(r"昵称|别名"),
                    "uid" @ RegexMatch(r"\d+", optional=True),
                    "nick" @ WildcardMatch(optional=True),
                ]
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def main(
    app: Ariadne, group: Group, act: RegexResult, uid: RegexResult, nick: RegexResult
):
    if uid.matched:
        uids = uid.result.display
        if uids.isdigit():
            nicks = nick.result.display
            if len(nicks) > 24:
                msg = "昵称过长，设定失败"
            acts = act.result.display
            if acts == "设定":
                msg = "昵称设定成功" if set_nick(uids, group.id, nicks) else "该群未关注此 UP"
            elif acts == "删除":
                msg = "昵称删除成功" if set_nick(uids, group.id, None) else "该群未关注此 UP"
        else:
            msg = "请输入正确的 UID"
    else:
        msg = "请输入正确的 UID"

    await app.send_group_message(group, MessageChain(msg))