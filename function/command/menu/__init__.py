from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    RegexMatch,
)

from library.text2image import text2image
from core.control import Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r"([/.。?？!！])?(帮助|菜单|help|menu)([/.。?？!！])?"),
                ]
            )
        ],
        decorators=[Permission.require(), Interval.require()],
    )
)
async def main(app: Ariadne, group: Group):

    help = (
        "BBot 功能菜单：\n"
        "=================================================================\n"
        " 0. /quit\n"
        " 1. BiliBili 视频解析\n"
        " 2. 查看关注列表\n"
        " 3. 关注 <uid>\n    > (订阅|关注)(主播|[uU][pP])?\n"
        " 4. 取关 <uid>\n    > (退订|取消?关注?)\\s?(主播|[uU][pP])?\n"
        " 5. 查看动态 <uid>\n"
        " 6. 设定|删除 昵称 <uid> [昵称]\n"
        " 7. 开启|关闭 @全体成员 <uid>\n"
        "=================================================================\n"
        "BBot 采用 gRPC 接口进行动态检查，关注后目标 UP 将粉丝数 +1，收到动态更新后 BBot 将会对动态点赞。"
    )

    await app.sendGroupMessage(
        group,
        MessageChain.create(Image(data_bytes=await text2image(help))),
    )
