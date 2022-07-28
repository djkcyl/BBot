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

from core import BOT_Status
from library import subscribe_uid
from core.bot_config import BotConfig
from library.uid_extract import uid_extract
from core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r"(订阅|关注)(主播|[uU][pP])?"),
                    "anything" @ WildcardMatch(optional=True),
                ]
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def main(app: Ariadne, group: Group, anything: RegexResult):

    if not anything.matched:
        return
    message = anything.result.display
    uid = await uid_extract(message)
    if uid:
        if BOT_Status["dynamic_updateing"]:
            await app.send_group_message(
                group,
                MessageChain("正在订阅，请稍后..."),
            )
        msg = await subscribe_uid(uid, group.id)
        await app.send_group_message(
            group,
            MessageChain(msg),
        )
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(f"群：{group.name}（{group.id}）\n正在订阅 UP：{uid}\n{msg}"),
        )
    else:
        await app.send_group_message(
            group,
            MessageChain("未找到该 UP，请输入正确的 UP 群内昵称、UP 名、UP UID或 UP 首页链接"),
        )
