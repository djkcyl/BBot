from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import BotJoinGroupEvent
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core.bot_config import BotConfig
from core.group_config import GroupPermission

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def main(app: Ariadne, joingroup: BotJoinGroupEvent):
    """
    收到入群事件
    """
    group = joingroup.group
    gp = GroupPermission(group)
    msg = [f"收到入群事件：{joingroup.group.name}（{joingroup.group.id}）"]
    if joingroup.inviter:
        msg.append(f"邀请者：{joingroup.inviter.name}（{joingroup.inviter.id}）")
    if gp.can_join():
        for admin in BotConfig.admins:
            await app.send_friend_message(
                admin,
                MessageChain(
                    msg,
                    "已自动加入",
                ),
            )
    else:
        await app.quit_group(group)
        for admin in BotConfig.admins:
            await app.send_friend_message(
                admin,
                MessageChain(
                    msg,
                    "该群不在白名单中，已自动退出",
                ),
            )
