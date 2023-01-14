from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_seconds

from ...core import BOT_Status

channel = Channel.current()
offline = False


@channel.use(SchedulerSchema(every_custom_seconds(0)))
async def mirai_disconnect(app: Ariadne):
    global offline
    if BOT_Status["started"]:
        if app.connection.status.connected:
            if not BOT_Status["init"] and offline:
                BOT_Status["init"] = True
                offline = False
                logger.info("Bot 连接成功")
        elif BOT_Status["init"] and not offline:
            BOT_Status["init"] = False
            offline = True
            logger.info("Bot 断开连接")
