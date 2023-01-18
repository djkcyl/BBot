from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema

from ...core.bot_config import BotConfig
from ...utils.get_project_version import get_local_version, get_remote_version


channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("0 12 * * *")))
async def main(app: Ariadne):
    remote_version = await get_remote_version()
    local_version = get_local_version()

    logger.warning(f"[版本更新] 检测到新版本：{local_version} > {remote_version}")

    if local_version and remote_version and local_version < remote_version:
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(f"检测到 BBot 版本更新：{local_version} > {remote_version}，请及时更新以避免出现问题。"),
        )
