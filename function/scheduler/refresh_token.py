import json
import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema

from core import BOT_Status
from core.bot_config import BotConfig
from library.bilibili_request import save_token, set_token, token_refresh


channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("0 0 1 * *")))
async def main(app: Ariadne):
    logger.info("[BiliBili推送] 开始刷新 token")
    BOT_Status["init"] = False

    while BOT_Status["live_updateing"] or BOT_Status["dynamic_updateing"]:
        await asyncio.sleep(0.1)

    resp = await token_refresh()
    if resp["code"] == 0:
        set_token(resp)
        save_token()
        logger.success(f"[BiliBili推送] 刷新 token 成功，token：{resp['data']['token_info']}")
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(
                f"[BiliBili推送] 刷新 token 成功\n{json.dumps(resp['data']['token_info'], indent=2)}"
            ),
        )
    else:
        logger.error(f"[BiliBili推送] 刷新 token 失败，{resp}")
        await app.send_friend_message(
            BotConfig.master,
            MessageChain(f"[BiliBili推送] 刷新 token 失败，Bot 已关机，{resp}"),
        )
        app.stop()
    BOT_Status["init"] = True
