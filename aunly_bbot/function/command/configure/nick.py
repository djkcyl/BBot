from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.element import At
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
    ParamMatch,
    RegexResult,
    ElementMatch,
    ElementResult,
)

from ....core.bot_config import BotConfig
from ....utils.up_operation import set_nick
from ....utils.uid_extract import uid_extract
from ....core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    "at" @ ElementMatch(At, optional=True),
                    "act" @ RegexMatch(r"设定|删除"),
                    RegexMatch(r"昵称|别名"),
                    "uid" @ ParamMatch(optional=True),
                    "nick" @ ParamMatch(optional=True),
                ]
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def main(
    app: Ariadne,
    group: Group,
    at: ElementResult,
    act: RegexResult,
    uid: RegexResult,
    nick: RegexResult,
):
    if at.result:
        at_element: At = at.result  # type: ignore
        if at_element.target != BotConfig.Mirai.account:
            return

    if uid.matched:
        uid = await uid_extract(uid.result.display, group.id)
        if uid:
            acts = act.result.display
            if acts == "设定":
                nicks = nick.result.display
                if len(nicks) > 24:
                    msg = "昵称过长，设定失败"
                else:
                    msg = f"{uid} 昵称设定成功" if set_nick(uid, group.id, nicks) else "该群未关注此 UP"
            else:
                msg = f"{uid} 昵称删除成功" if set_nick(uid, group.id, None) else "该群未关注此 UP"
        else:
            msg = "请输入正确的 UID"
    else:
        msg = "请输入正确的 UID"

    await app.send_group_message(group, MessageChain(msg))
