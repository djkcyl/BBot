from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.exceptions import PropagationCancelled
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

from core.subgroup_config import get_subgroup_list
from core.control import Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                RegexMatch(r"(查看)?订阅组列表")
            )
        ],
    )
)
async def sub_list(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)

    groupNames, sub_lists = get_subgroup_list()
    group_name_count = len(groupNames)
    if group_name_count == 0:
        await app.sendFriendMessage(friend, MessageChain.create("当前未创建订阅组"))
    else:
        # TODO 需要考虑是否增加up主名称显示
        msg = [f"当前共创建订阅组 {group_name_count} 个"]
        for i, data in enumerate(groupNames, 1):
            groupName = data
            sublist = sub_lists[i - 1]
            msg.append(f"\n{i}. {f'{groupName}'}（{sublist}）")
        await app.sendFriendMessage(friend, MessageChain.create(msg))

    raise PropagationCancelled
