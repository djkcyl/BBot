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
async def main(app: Ariadne, group: Group, message: MessageChain, anything: RegexResult):

    if not (uid := await uid_extract(anything.result.display, group.id)):
        return await app.send_group_message(
            group,
            MessageChain("未找到该 UP，请输入正确的 UP 群内昵称、UP 名、UP UID或 UP 首页链接"),
            quote=message,
        )

    res = await grpc_dyn_get(uid)
    if res.list:
        if len(res.list) > 1:
            if res.list[0].modules[0].module_author.is_top:
                dyn_id = res.list[1].extend.dyn_id_str
            else:
                dyn_id = res.list[0].extend.dyn_id_str
        else:
            dyn_id = res.list[0].extend.dyn_id_str
        shot_image = await get_dynamic_screenshot(dyn_id)
        return await app.send_group_message(
            group, MessageChain(Image(data_bytes=shot_image)), quote=message
        )
    await app.send_group_message(group, MessageChain("该 UP 未发布任何动态"), quote=message)
