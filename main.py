import sys
import asyncio
import contextlib

from creart import it
from pathlib import Path
from loguru import logger
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from prompt_toolkit.styles import Style
from graia.ariadne.console import Console
from graia.scheduler import GraiaScheduler
from prompt_toolkit.formatted_text import HTML
from graia.ariadne.console.saya import ConsoleBehaviour
from graia.ariadne.entry import config, HttpClientConfig, WebsocketClientConfig

from core.bot_config import BotConfig

LOGPATH = Path("logs")
LOGPATH.mkdir(exist_ok=True)
logger.add(
    LOGPATH.joinpath("latest.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="1 years",
    compression="tar.xz",
    colorize=False,
    level="INFO",
)

logger.add(
    LOGPATH.joinpath("debug.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="15 days",
    compression="tar.xz",
    colorize=False,
    level="DEBUG",
)

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

console = Console(
    broadcast=app.broadcast,
    prompt=HTML("<bbot> BBot </bbot>> "),
    style=Style(
        [
            ("bbot", "fg:#ffffff"),
        ]
    ),
)


app.create(GraiaScheduler)
saya = it(Saya)
saya.install_behaviours(ConsoleBehaviour(console))


with saya.module_context():

    saya.require("function")

import function  # noqa: E402 F401

with contextlib.suppress(KeyboardInterrupt, asyncio.exceptions.CancelledError):
    app.launch_blocking()
logger.info("BBot is shutting down...")
