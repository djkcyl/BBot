import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.mirai import (
    BotLeaveEventKick,
    BotLeaveEventActive,
    BotLeaveEventDisband,
)

from core.bot_config import BotConfig
from core.group_config import GroupPermission
from library import get_group_sublist, unsubscribe_uid

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[BotLeaveEventKick, BotLeaveEventActive, BotLeaveEventDisband]
    )
)
async def main(app: Ariadne, group: Group):
    GroupPermission(group).remove_from_whitelist()
    logger.info(f"[BiliBili推送] 检测到退群事件 > {group.name}({group.id})，正在删除该群的订阅")
    remove_list = []
    for subid, _, _ in get_group_sublist(group.id):
        unsubscribe_uid(subid, group.id)
        remove_list.append(subid)
        logger.info(f"[BiliBili推送] 已删除订阅 > {subid}")
        await asyncio.sleep(2)
    logger.info(
        f"[BiliBili推送] 检测到退群事件 > {group.name}({group.id})，已删除该群订阅的 {len(remove_list)} 个 UP"
    )
    for qq in BotConfig.admins:
        await app.send_friend_message(
            qq,
            MessageChain(
                "收到被踢出群聊事件",
                f"\n群号：{group.id}",
                f"\n群名：{group.name}",
                f"\n已移出白名单并删除该群订阅的 {len(remove_list)} 个 UP",
            ),
        )
