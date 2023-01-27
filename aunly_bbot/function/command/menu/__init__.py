from loguru import logger
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
    ElementMatch,
    ElementResult,
)

from ....core.bot_config import BotConfig
from ....utils.text2image import text2image
from ....core.control import Interval, Permission

channel = Channel.current()
menu_image = None
help_text = (
    "BBot 功能菜单：\n"
    "=================================================================\n"
    " 0. /quit\n"
    " 1. BiliBili 视频解析\n"
    " 2. 查看关注列表\n"
    f" 3. @{BotConfig.name} 关注 <uid>\n    > @{BotConfig.name} (订阅|关注)(主播|[uU][pP])?\n"
    f" 4. @{BotConfig.name} 取关 <uid>\n    > @{BotConfig.name} (退订|取消?关注?)\\s?(主播|[uU][pP])?\n"
    " 5. 查看动态 <uid> <offset>\n    > offset 可以填写数字，用来代表该 UP 的倒数第几条动态\n"
    " 6. 设定|删除 昵称 <uid> [昵称]\n"
    " 7. 开启|关闭 @全体成员 <uid>\n"
    "=================================================================\n"
    "BBot 采用 gRPC 接口进行动态检查。"
)

if BotConfig.Bilibili.use_login:
    help_text += "关注后目标 UP 将粉丝数 +1，收到动态更新后 BBot 将会对动态点赞。"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    "at" @ ElementMatch(At, optional=True),
                    RegexMatch("([/.。?？!！])?(帮助|菜单|功能|help|menu)([/.。?？!！])?"),
                ]
            )
        ],
        decorators=[Permission.require(), Interval.require()],
        priority=15,
    )
)
async def main(app: Ariadne, group: Group, at: ElementResult):
    if at.result:
        at_element: At = at.result  # type: ignore
        if at_element.target != BotConfig.Mirai.account:
            return

    global menu_image

    if not menu_image:
        logger.info("正在生成菜单图片")
        menu_image = await app.upload_image(await text2image(help_text))

    await app.send_group_message(group, MessageChain(menu_image))
