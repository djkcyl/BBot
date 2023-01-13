from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.mirai import BotInvitedJoinGroupRequestEvent

from ...core.bot_config import BotConfig
from ...core.group_config import GroupPermission

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
async def main(app: Ariadne, event: BotInvitedJoinGroupRequestEvent):
    """
    收到入群事件
    """
    gp = GroupPermission(event.source_group)
    msg = [
        f"收到入群邀请事件：{event.group_name}（{event.source_group}）\n",
        f"邀请来源：{event.nickname}（{event.supplicant}）\n",
    ]
    if gp.can_join():
        await event.accept()
        for admin in BotConfig.admins:
            try:
                await app.send_friend_message(
                    admin,
                    MessageChain(
                        msg,
                        "已自动同意加入",
                    ),
                )
            except UnknownTarget:
                logger.warning(f"由于未添加 {admin} 为好友，无法发送通知")
    else:
        await event.reject()
        for admin in BotConfig.admins:
            try:
                await app.send_friend_message(
                    admin,
                    MessageChain(
                        msg,
                        "该群不在白名单中，已拒绝加入",
                    ),
                )
            except UnknownTarget:
                logger.warning(f"由于未添加 {admin} 为好友，无法发送通知")
