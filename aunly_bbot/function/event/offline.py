from typing import Union
from loguru import logger
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.lifecycle import AccountLaunch, AccountShutdown, AccountConnectionFail

from ...core import BOT_Status, Status

channel = Channel.current()


@channel.use(
    ListenerSchema(listening_events=[AccountLaunch, AccountShutdown, AccountConnectionFail])
)
async def mirai_disconnect(event: Union[AccountLaunch, AccountShutdown, AccountConnectionFail]):
    if isinstance(event, AccountLaunch):
        if not BOT_Status.check_status(Status.ACCOUNT_CONNECTED):
            logger.info("[Mirai] 账号已连接成功")
            BOT_Status.set_status(Status.ACCOUNT_CONNECTED, True)
    elif BOT_Status.check_status(Status.ACCOUNT_CONNECTED):
        logger.warning("[Mirai] 账号断开")
        BOT_Status.set_status(Status.ACCOUNT_CONNECTED, False)
