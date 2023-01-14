import asyncio

from creart import it
from typing import Union
from graia.saya import Channel, Saya
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

from ...core.control import Interval, Permission
from ...utils.strings import generate_verify_code

saya = Saya.current()
channel = Channel.current()
inc = it(InterruptControl)


class ConfirmWaiter(Waiter.create([GroupMessage], block_propagation=True)):
    def __init__(self, group: Union[Group, int], member: Union[Member, int], verify: str):
        self.group = group if isinstance(group, int) else group.id
        self.member = member if isinstance(member, int) else member.id
        self.verify = verify

    async def detected_event(
        self, app: Ariadne, group: Group, member: Member, message: MessageChain
    ):
        if self.group == group.id and self.member == member.id:
            msg = message.display
            if msg == self.verify:
                return True
            elif msg == "/quit cancel":
                return False
            else:
                await app.send_group_message(
                    self.group, MessageChain("请输入正确的验证码，或者发送 /quit cancel 来取消")
                )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(RegexMatch(r"([/.。?？!！])quit"))],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require(20)],
    )
)
async def main(app: Ariadne, group: Group, member: Member):
    verify_code = generate_verify_code()
    await app.send_group_message(group, MessageChain(f"正在请求退出本群，请在30秒内输入验证码 {verify_code}"))
    try:
        res = await inc.wait(
            ConfirmWaiter(group, member, verify_code),
            timeout=30,
        )
    except asyncio.TimeoutError:
        res = False

    if res:
        await app.send_group_message(group, MessageChain("正在退出"))
        await asyncio.sleep(3)
        await app.quit_group(group)
    else:
        await app.send_group_message(group, MessageChain("已取消退群"))
