import sys
import asyncio
import contextlib

from creart import it
from pathlib import Path
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.scheduler import GraiaScheduler
from graia.ariadne.entry import config, HttpClientConfig, WebsocketClientConfig

from core.bot_config import BotConfig
from core.log import logger

logger.info("BBot is starting...")

try:
    host = BotConfig.Mirai.mirai_host
    app_config = config(
        BotConfig.Mirai.account,
        BotConfig.Mirai.verify_key,
        HttpClientConfig(host),
        WebsocketClientConfig(host),
    )
except (AssertionError, TypeError):
    logger.critical("请检查配置文件（data/bot_group.yaml）是否有误")
    sys.exit(1)

app = Ariadne(app_config)
app.create(GraiaScheduler)
saya = it(Saya)


with saya.module_context():

    saya.require("function")

import function  # noqa: E402 F401

with contextlib.suppress(KeyboardInterrupt, asyncio.exceptions.CancelledError):
    app.launch_blocking()
logger.info("BBot is shutting down...")
