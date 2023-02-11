from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema

from ...core.bot_config import BotConfig
from ...utils.update_version import update_version


channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("0 12 * * *")))
async def main(app: Ariadne):
    logger.info("[版本更新] 正在检查版本更新...")

    update = await update_version()

    if update:
        old_version, new_version = update
        logger.warning(f"[版本更新] 检测到新版本：{new_version} > {old_version}")
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(f"检测到 BBot 版本更新：{new_version} > {old_version}，建议及时更新以避免出现问题并获取最新功能。"),
        )
