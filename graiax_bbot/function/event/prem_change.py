from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.mirai import BotGroupPermissionChangeEvent

from ...core.bot_config import BotConfig

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[BotGroupPermissionChangeEvent]))
async def main(app: Ariadne, event: BotGroupPermissionChangeEvent):
    """
    群内权限变动
    """
    if BotConfig.Event.permchange:
        for admin in BotConfig.admins:
            try:
                await app.send_friend_message(
                    admin,
                    MessageChain(
                        "收到权限变动事件",
                        f"\n群号：{event.group.id}",
                        f"\n群名：{event.group.name}",
                        f"\n权限变更为：{event.current}",
                    ),
                )
            except UnknownTarget:
                logger.warning(f"由于未添加 {admin} 为好友，无法发送通知")
