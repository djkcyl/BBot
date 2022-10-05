import os
import sys
from loguru import logger
import psutil
import sentry_sdk

from pathlib import Path

from core import Bot_Config
from core.bot_config import _BotConfig

sentry_sdk.init(
    dsn="https://e7455ef7813c42e2b854bdd5c26adeb6@o1418272.ingest.sentry.io/6761179",
    traces_sample_rate=1.0,
)

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    s = psutil.Process().parent()
    if s.name() == "explorer.exe" or s.parent().name() == "explorer.exe":
        Path("start.bat").write_text(
            """@echo off
title BBot for Ariadne
@REM 自动搜索路径里名称包含 bbot 的 exe 并执行
for /f "tokens=*" %%a in ('dir /b /s /a-d bbot*.exe') do (
    echo 正在运行 %%a
    %%a
    pause
    exit
)"""
        )
        print("请在命令行中运行 .exe 文件")
        print("Please run .exe file in command line")
        print("已生成 start.bat 文件")
        print("Generated start.bat file")
        input("按回车键退出 Press Enter to exit")
        sys.exit(1)

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = Path("data", "browser").absolute().as_posix()


# if not Bot_Config.verify():
if 1:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    app = FastAPI()
    port = os.getenv("BBOT_WEBUI_PORT", 8090)

    @app.get("/api/config/load")
    async def load_config():
        return

    @app.post("/api/config/save")
    async def save_config(config: _BotConfig):
        try:
            Bot_Config.save(config)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.get("/api/config/stop")
    async def stop_uvicorn():
        # 发送 SIGINT 信号给 uvicorn
        os.kill(os.getpid(), 2)
        return {"status": "ok"}

    @app.get("/")
    async def index():
        return FileResponse(Path("website", "static", "init", "index.html"))

    app.mount("/", StaticFiles(directory=Path("website", "static", "init")), name="Init Page")

    logger.warning(f"由于配置文件不存在或不完整，请打开浏览器访问 BBot 主机的 {port} 端口进行配置")
    uvicorn.run(app, host="0.0.0.0", port=int(port))

import bot
