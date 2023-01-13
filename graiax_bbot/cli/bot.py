import sys
import asyncio
import contextlib

from loguru import logger

from ..bot import app
from ..core.bot_config import BotConfig


def run():
    if BotConfig.master == 123456789 or BotConfig.Mirai.verify_key == "xxxxxxxxx":
        logger.critical("请先完成 BBot 配置")
        sys.exit(1)
    with contextlib.suppress(KeyboardInterrupt, asyncio.exceptions.CancelledError):
        app.launch_blocking()
    logger.info("BBot is shut down.")
