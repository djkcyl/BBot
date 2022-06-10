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

from library import unsubscribe_uid
from library import get_group_sublist
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
                    RegexMatch(r"(退订|取消?关注?)\s?(主播|[uU][pP])?"),
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
        uid = uid
    else:
        if not (up_list := get_group_sublist(group.id)):
            return await app.send_group_message(
                group, MessageChain(f"本群未订阅该 UP（{message}）")
            )

        for up_uid, up_name, up_nick in up_list:
            if up_nick == message or up_name == message:
                uid = up_uid
                break
        else:
            return await app.send_group_message(
                group, MessageChain(f"本群未订阅该 UP（{message}）")
            )

    if uid:
        msg = await unsubscribe_uid(uid, group.id)
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(f"群 {group.name}（{group.id}）正在退订 UP：{uid}\n{msg}"),
        )
        await app.send_group_message(
            group,
            MessageChain(msg),
        )
    else:
        await app.send_group_message(
            group,
            MessageChain("请输入正确的 UP 名、UP UID 或 UP 首页链接"),
        )