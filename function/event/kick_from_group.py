from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import BotLeaveEventKick
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core.bot_config import BotConfig
from core.group_config import GroupPermission
from library import get_group_sublist, unsubscribe_uid

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[BotLeaveEventKick]))
async def main(app: Ariadne, group: Group):
    GroupPermission(group).remove_from_whitelist()
    remove_list = []
    for subid, _, _ in get_group_sublist(group.id):
        unsubscribe_uid(subid, group.id)
        remove_list.append(subid)
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
                "\n已移出白名单并退订该群的所有 UP",
            ),
        )