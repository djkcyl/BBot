import asyncio
import contextlib

from pathlib import Path
from loguru import logger
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from prompt_toolkit.styles import Style
from graia.ariadne.console import Console
from graia.scheduler import GraiaScheduler
from graia.ariadne.model import MiraiSession
from prompt_toolkit.formatted_text import HTML
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.console.saya import ConsoleBehaviour
from graia.scheduler.saya import GraiaSchedulerBehaviour
from graia.saya.builtins.broadcast import BroadcastBehaviour

from core.bot_config import BotConfig


LOGPATH = Path("logs")
LOGPATH.mkdir(exist_ok=True)
logger.add(
    LOGPATH.joinpath("latest.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="3 years",
    compression="tar.xz",
    colorize=False,
)
logger.info("BBot is starting...")


app = Ariadne(
    MiraiSession(
        host=BotConfig.Mirai.mirai_host,
        verify_key=BotConfig.Mirai.verify_key,
        account=BotConfig.Mirai.account,
    ),
)

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
saya = app.create(Saya)
saya.install_behaviours(
    app.create(BroadcastBehaviour),
    app.create(GraiaSchedulerBehaviour),
    ConsoleBehaviour(console),
    app.create(InterruptControl),
)


with saya.module_context():

    saya.require("function.command.quit_group")
    saya.require("function.command.video_resolve")
    saya.require("function.command.vive_dynamic")

    saya.require("function.command.admin.add")
    saya.require("function.command.admin.remove")

    saya.require("function.command.configure.atall")
    saya.require("function.command.configure.nick")

    saya.require("function.command.menu")

    saya.require("function.command.up.get_subscribe")
    saya.require("function.command.up.subscribe")
    saya.require("function.command.up.unsubscribe")

    saya.require("function.command.whitelist.add")
    saya.require("function.command.whitelist.close")
    saya.require("function.command.whitelist.open")
    saya.require("function.command.whitelist.remove")

    saya.require("function.console.stop")

    saya.require("function.event.bot_launch")
    saya.require("function.event.exception")
    saya.require("function.event.invited_join_group")
    saya.require("function.event.join_group")
    saya.require("function.event.kick_from_group")
    saya.require("function.event.mute")
    saya.require("function.event.new_friend")
    saya.require("function.event.prem_change")

    saya.require("function.pusher.init")
    saya.require("function.pusher.dynamic")
    saya.require("function.pusher.live")


with contextlib.suppress(KeyboardInterrupt, asyncio.exceptions.CancelledError):
    app.launch_blocking()
logger.info("BBot is shutting down...")
