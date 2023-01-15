from loguru import logger
from typing import Optional
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import NewFriendRequestEvent
from graia.saya.builtins.broadcast.schema import ListenerSchema

from ...core.bot_config import BotConfig

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[NewFriendRequestEvent]))
async def main(app: Ariadne, event: NewFriendRequestEvent):
    """
    收到新好友事件
    """
    source_group: Optional[int] = event.source_group
    group_name = await app.get_group(source_group) if source_group else None
    group_name = group_name.name if group_name else "未知"
    for admin in BotConfig.admins:
        try:
            await app.send_friend_message(
                admin,
                MessageChain(
                    "收到添加好友事件",
                    f"\nQQ：{event.supplicant}",
                    f"\n昵称：{event.nickname}",
                    f"\n来自群：{group_name}({source_group})" if source_group else "\n来自好友搜索",
                    "\n状态：已通过申请\n",
                    event.message or "无附加信息",
                ),
            )
        except UnknownTarget:
            logger.warning(f"由于未添加 {admin} 为好友，无法发送通知")

    await event.accept()
