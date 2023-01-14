import contextlib

from loguru import logger
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from graia.ariadne.message.element import AtAll
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.chain import MessageChain
from typing import Optional, TypeVar, Union, overload
from graia.ariadne.event.message import ActiveMessage
from graia.ariadne.model import Friend, Group, Member
from graia.ariadne.typing import SendMessageAction, SendMessageException
from graia.ariadne.exception import UnknownTarget, AccountMuted, RemoteException

from core import BOT_Status
from core.context import Context
from core.bot_config import BotConfig

from .up_operation import delete_group

Exc_T = TypeVar("Exc_T", bound=SendMessageException)


class Safe(SendMessageAction):
    """
    安全发送的 SendMessage action
    """

    @overload
    @staticmethod
    async def exception(item) -> ActiveMessage:
        ...

    @overload
    async def exception(self, item) -> ActiveMessage:
        ...

    @staticmethod
    async def _handle(item: SendMessageException):

        push_type = "动态" if Context.push_type.get() == "dynamic" else "直播"
        push_id = Context.push_id.get()
        chain: MessageChain = item.send_data["message"]
        target: Union[Friend, Group, Member] = item.send_data["target"]
        ariadne = Ariadne.current()

        if isinstance(target, Group):
            if isinstance(item, UnknownTarget):
                logger.error(
                    f"[BiliBili推送] {push_type} {push_id} | 推送失败，找不到该群 {target.id}，正在取消订阅"
                )
                delete = await delete_group(target.id)
                logger.warning(f"[BiliBili推送] 已删除群 {target.id} 订阅的 {len(delete)} 个 UP")
                await ariadne.send_friend_message(
                    BotConfig.master,
                    MessageChain(
                        f"{push_type} {push_id} | 推送失败，找不到该群，已删除群 {target.id} 订阅的 {len(delete)} 个 UP"
                    ),
                )
                with contextlib.suppress(UnknownTarget):
                    await ariadne.quit_group(int(target.id))
            elif isinstance(item, AccountMuted):
                group = f"{target.name}（{target.id}）"
                msg = f"{push_type} {push_id} | 推送失败，Bot 在 {group} 被禁言"
                logger.warning(f"[BiliBili推送] {msg}")
                await ariadne.send_friend_message(BotConfig.master, MessageChain(msg))
            elif isinstance(item, RemoteException):
                if "resultType=46" in str(item):
                    msg = f"{push_type} {push_id} | 推送失败，Bot 被限制发送群聊消息（46 代码），请尽快处理后发送 /init 重新开启推送进程"
                    logger.error(f"[BiliBili推送] {msg}")
                    await ariadne.send_friend_message(BotConfig.master, MessageChain(msg))
                    BOT_Status["init"] = False
                    raise ExecutionStop()
                elif "resultType=110" in str(item):  # 110: 可能为群被封
                    logger.warning(f"[BiliBili推送] {push_type} {push_id} | 推送失败，Bot 因未知原因被移出群聊")
                    delete = await delete_group(target.id)
                    logger.warning(f"[BiliBili推送] 已删除群 {target.id} 订阅的 {len(delete)} 个 UP")
                    await ariadne.send_friend_message(
                        BotConfig.master,
                        MessageChain(
                            f"{push_type} {push_id} | 推送失败，Bot 因未知原因被移出群聊，已删除群 {target.id} 订阅的 {len(delete)} 个 UP"
                        ),
                    )
                    with contextlib.suppress(UnknownTarget):
                        await ariadne.quit_group(target.id)
                elif "reason=AT_ALL_LIMITED" in str(item):
                    msg = f"{push_type} {push_id} | 推送失败，Bot 在该群 @全体成员 次数已达上限"
                    logger.warning(f"[BiliBili推送] {msg}")
                    await ariadne.send_friend_message(
                        target.id,
                        MessageChain([e for e in chain.__root__ if not isinstance(e, AtAll)]),
                    )
                else:
                    capture_exception()
                    logger.exception(f"[BiliBili推送] {push_type} {push_id} | 推送失败，未知错误")

    @overload
    @staticmethod
    async def exception(s, i):
        ...

    @overload
    async def exception(s, i):  # sourcery skip: instance-method-first-arg-name
        ...

    async def exception(s: Union["Safe", Exc_T], i: Optional[Exc_T] = None):  # type: ignore
        # sourcery skip: instance-method-first-arg-name
        if not isinstance(s, Safe):
            return await Safe._handle(s)
        if i:
            return await Safe._handle(i)
