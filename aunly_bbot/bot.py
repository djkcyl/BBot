import os
import sys
import asyncio

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

from .core import cache
from .core.log import logger
from .website import BotWebService
from .core.bot_config import BotConfig
from .utils.fastapi import FastAPIService
from .utils.fonts_provider import get_font
from .utils.verify_mah import verify_mirai
from .utils.detect_package import is_package
from .core.announcement import base_telemetry


os.environ["PLAYWRIGHT_BROWSERS_PATH"] = (
    "0" if is_package else Path(__file__).parent.joinpath("static", "browser").as_posix()
)
logger.info("BBot is starting...")

base_telemetry()

logger.info("正在下载字体...")
asyncio.run(get_font())
logger.success("字体下载完成！")

host = BotConfig.Mirai.mirai_host
if verify_mirai(host, BotConfig.Mirai.account, BotConfig.Mirai.verify_key):
    logger.success("Mirai HTTP API 验证成功！")
else:
    sys.exit(1)
app_config = config(
    BotConfig.Mirai.account,
    BotConfig.Mirai.verify_key,
    HttpClientConfig(host),
    WebsocketClientConfig(host),
)

app = Ariadne(app_config)
app.config(install_log=True)

app.launch_manager.add_service(
    PlaywrightService(
        browser_type="firefox",
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
app.launch_manager.add_service(BotWebService())

app.create(GraiaScheduler)
saya = it(Saya)


with saya.module_context():
    if cache.get("test"):
        logger.info("正在进入测试模式...")
        saya.require("aunly_bbot.test")
    else:
        saya.require("aunly_bbot.function")

from . import function  # noqa
