import json
import asyncio

from pathlib import Path
from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from bilireq.login import refresh_token
from bilireq.utils import ResponseCodeError
from graia.scheduler.timers import crontabify
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema

from ...core.bot_config import BotConfig
from ...core import BOT_Status, Bili_Auth


channel = Channel.current()
login_cache_file = Path("data/login_cache.json")


@channel.use(SchedulerSchema(crontabify("0 0 * * *")))
async def main(app: Ariadne):
    logger.info("[BiliBili推送] 开始刷新 token")
    if BotConfig.Bilibili.use_login:
        BOT_Status["init"] = False

        while BOT_Status["live_updating"] or BOT_Status["dynamic_updating"]:
            await asyncio.sleep(0.1)

        try:
            resp = await refresh_token(auth=Bili_Auth)
            Bili_Auth.update(resp)
            logger.debug(await Bili_Auth.get_info())
            login_cache_file.write_text(
                json.dumps(dict(Bili_Auth), indent=2, ensure_ascii=False)
            )
            logger.success(f"[BiliBili推送] 刷新 token 成功，token：{resp['token_info']}")
            await app.send_friend_message(
                BotConfig.master,
                MessageChain(
                    f"[BiliBili推送] 刷新 token 成功\n{json.dumps(resp['token_info'], indent=2)}"
                ),
            )
        except ResponseCodeError as e:
            logger.error(f"[BiliBili推送] 刷新 token 失败，{e}")
            await app.send_friend_message(
                BotConfig.master,
                MessageChain(f"[BiliBili推送] 刷新 token 失败，Bot 已关机，{e}"),
            )
            app.stop()
        BOT_Status["init"] = True
    else:
        logger.info("[BiliBili推送] 未启用登录，跳过 token 刷新")
