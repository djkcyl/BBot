import asyncio
import contextlib

from creart import it
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.scheduler import GraiaScheduler
from graia.ariadne.entry import config, HttpClientConfig, WebsocketClientConfig

from core.log import logger
from core.bot_config import BotConfig
from core.announcement import base_telemetry

logger.info("BBot is starting...")

base_telemetry()

host = BotConfig.Mirai.mirai_host
app_config = config(
    BotConfig.Mirai.account,
    BotConfig.Mirai.verify_key,
    HttpClientConfig(host),
    WebsocketClientConfig(host),
)

app = Ariadne(app_config)
app.config(install_log=True)
app.create(GraiaScheduler)
saya = it(Saya)


with saya.module_context():

    saya.require("function")

import function  # noqa: E402 F401

with contextlib.suppress(KeyboardInterrupt, asyncio.exceptions.CancelledError):
    app.launch_blocking()
logger.info("BBot is shutting down...")
