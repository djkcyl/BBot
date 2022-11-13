import asyncio
import contextlib

from creart import it
from pathlib import Path
from graia.saya import Saya
from fastapi import FastAPI
from graia.ariadne.app import Ariadne
from graia.scheduler import GraiaScheduler
from graiax.playwright.service import PlaywrightService
from graia.amnesia.builtins.uvicorn import UvicornService
from graia.amnesia.builtins.memcache import MemcacheService
from graia.ariadne.entry import config, HttpClientConfig, WebsocketClientConfig

from main import BotConfig
from core.log import logger
from website import BotService
from library.fastapi import FastAPIService
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

if BotConfig.Bilibili.use_browser:
    app.launch_manager.add_service(
        PlaywrightService(
            user_data_dir=Path("data").joinpath("browser"),
            device_scale_factor=2 if BotConfig.Bilibili.mobile_style else 1.25,
            user_agent=(
                "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36"
            )
            if BotConfig.Bilibili.mobile_style
            else "",
        )
    )
app.launch_manager.add_service(MemcacheService())
app.launch_manager.add_service(
    FastAPIService(
        FastAPI(
            title="BBot API",
            description="适用于 BBot WebUI 的 API 文档",
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
        )
    )
)
app.launch_manager.add_service(
    UvicornService(host=BotConfig.Webui.webui_host, port=int(BotConfig.Webui.webui_port))
)
app.launch_manager.add_service(BotService())

app.create(GraiaScheduler)
saya = it(Saya)


with saya.module_context():

    saya.require("function")

import function  # noqa

with contextlib.suppress(KeyboardInterrupt, asyncio.exceptions.CancelledError):
    app.launch_blocking()
logger.info("BBot is shut down.")
