import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.mirai import (
    BotLeaveEventKick,
    BotLeaveEventActive,
    BotLeaveEventDisband,
)

from ...core.bot_config import BotConfig
from ...core.data import get_sub_by_group
from ...core.group_config import GroupPermission
from ...utils.up_operation import unsubscribe_uid

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
    for data in get_sub_by_group(group.id):
        await unsubscribe_uid(data.uid, group.id)
        remove_list.append(data.uid)
        logger.info(f"[BiliBili推送] 已删除订阅 > {data.uid}")
        await asyncio.sleep(2)
    logger.info(
        f"[BiliBili推送] 检测到退群事件 > {group.name}({group.id})，已删除该群订阅的 {len(remove_list)} 个 UP"
    )
    for admin in BotConfig.admins:
        try:
            await app.send_friend_message(
                admin,
                MessageChain(
                    "收到退出群聊事件",
                    f"\n群号：{group.id}",
                    f"\n群名：{group.name}",
                    f"\n已移出白名单并删除该群订阅的 {len(remove_list)} 个 UP",
                ),
            )
        except UnknownTarget:
            logger.warning(f"由于未添加 {admin} 为好友，无法发送通知")
