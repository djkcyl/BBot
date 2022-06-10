import asyncio

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.mirai import BotMuteEvent
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core.bot_config import BotConfig
from core.group_config import GroupPermission

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[BotMuteEvent]))
async def main(app: Ariadne, group: Group, mute: BotMuteEvent):
    GroupPermission(group).remove_from_whitelist()
    if BotConfig.Event.mute:
        for qq in BotConfig.admins:
            await app.send_friend_message(
                qq,
                MessageChain(
                    "收到禁言事件，已退出该群",
                    f"\n群号：{group.id}",
                    f"\n群名：{group.name}",
                    f"\n操作者：{mute.operator.name} | {mute.operator.id}",
                ),
            )
            await asyncio.sleep(1)

    await app.quit_group(group)
