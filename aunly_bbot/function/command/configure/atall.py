from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import At
from graia.ariadne.model import Group, MemberPerm
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
from ....utils.up_operation import set_atall
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
                    "act" @ RegexMatch(r"开启|关闭"),
                    RegexMatch(r"@?全体(成员)?"),
                    "uid" @ ParamMatch(optional=True),
                ]
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def main(
    app: Ariadne, group: Group, at: ElementResult, act: RegexResult, uid: RegexResult
):
    if at.result:
        at_element: At = at.result  # type: ignore
        if at_element.target != BotConfig.Mirai.account:
            return

    if uid.matched:
        uid = await uid_extract(uid.result.display, group.id)
        if uid:
            acts = act.result.display
            if acts == "开启":
                if group.account_perm in [MemberPerm.Administrator, MemberPerm.Owner]:
                    msg = f"{uid} @全体开启成功" if set_atall(uid, group.id, True) else "该群未关注此 UP"
                else:
                    msg = "Bot 权限不足，无法开启@全体，请赋予 Bot 管理员权限或更高"
            else:
                msg = f"{uid} @全体关闭成功" if set_atall(uid, group.id, False) else "该群未关注此 UP"
        else:
            msg = "请输入正确的 UID"
    else:
        msg = "请输入正确的 UID"

    await app.send_group_message(group, MessageChain(msg))
