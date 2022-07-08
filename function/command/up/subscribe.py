import httpx

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
        uid = uid
    elif message.startswith("UID:"):
        uid = message[4:]
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.bilibili.com/x/web-interface/search/type",
                params={"keyword": message, "search_type": "bili_user"},
            )

        data = resp.json()["data"]
        if data["numResults"]:
            if data["result"][0]["uname"] == message:
                uid = data["result"][0]["mid"]
            else:
                return await app.send_group_message(
                    group,
                    MessageChain("请输入正确的 UP 名、UP UID 或 UP 首页链接"),
                )
        else:
            return await app.send_group_message(
                group,
                MessageChain("未搜索到该 UP"),
            )

    if BOT_Status["updateing"]:
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
        MessageChain(f"群 {group.name}（{group.id}）正在订阅 UP：{uid}\n{msg}"),
    )
