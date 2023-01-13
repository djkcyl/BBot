from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

from ....core.subgroup_config import get_subgroup_list
from ....core.control import Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight(RegexMatch(r"(查看)?订阅组(列表)?"))],
    )
)
async def sub_list(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)

    group_names, sub_lists = get_subgroup_list()
    group_name_count = len(group_names)
    if group_name_count == 0:
        await app.send_friend_message(friend, MessageChain("当前未创建订阅组"))
    else:
        # TODO 需要考虑是否增加up主名称显示
        msg = [f"当前共创建订阅组 {group_name_count} 个"]
        for i, data in enumerate(group_names, 1):
            group_name = data
            sublist = sub_lists[i - 1]
            msg.append(f"\n{i}. {f'{group_name}'}（{sublist}）")
        await app.send_friend_message(friend, MessageChain(msg))
