from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from library.grpc import grpc_dyn_get
from library.uid_extract import uid_extract
from core.control import Interval, Permission
from library.dynamic_shot import get_dynamic_screenshot

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("查看动态"), "anything" @ WildcardMatch()])],
        decorators=[Permission.require(), Interval.require(20)],
    )
)
async def main(app: Ariadne, group: Group, anything: RegexResult):

    if not (uid := await uid_extract(anything.result.display, group.id)):
        return await app.send_group_message(group, MessageChain("请输入正确的 UP UID 或 首页链接"))

    if res := await grpc_dyn_get(uid):
        shot_image = await get_dynamic_screenshot(res.list[0].extend.dyn_id_str)
        await app.send_group_message(group, MessageChain(Image(data_bytes=shot_image)))
    else:
        await app.send_group_message(group, MessageChain("该 UP 未发布任何动态"))
