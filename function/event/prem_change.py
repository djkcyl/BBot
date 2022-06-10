from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.mirai import BotGroupPermissionChangeEvent

from core.bot_config import BotConfig

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[BotGroupPermissionChangeEvent]))
async def main(app: Ariadne, event: BotGroupPermissionChangeEvent):
    """
    群内权限变动
    """
    if BotConfig.Event.permchange:
        for qq in BotConfig.admins:
            await app.send_friend_message(
                qq,
                MessageChain(
                    "收到权限变动事件",
                    f"\n群号：{event.group.id}",
                    f"\n群名：{event.group.name}",
                    f"\n权限变更为：{event.current}",
                ),
            )
