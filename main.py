import os
import sys
import psutil
from pathlib import Path
from loguru import logger
from sentry_sdk import init as sentry_sdk_init

from core.bot_config import _BotConfig
from utils.detect_package import is_package

sentry_sdk_init(
    dsn="https://e7455ef7813c42e2b854bdd5c26adeb6@o1418272.ingest.sentry.io/6761179",
    traces_sample_rate=1.0,
)

if is_package:
    s = psutil.Process().parent()
    if s.name() not in ["powershell.exe", "cmd.exe"]:
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

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = Path("static", "browser").as_posix()


# 加载配置项webui
def load_config_webui(reason: str = "未知原因", err: dict = {}):
    import uvicorn
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    def valueerror_output(err: dict):
        err_info = []
        pos_maxlen = 0
        for err_pos in err:
            err_msg = err[err_pos]
            pos_maxlen = max(pos_maxlen, len(err_pos))
            err_info.append([err_pos, err_msg])
        logger.critical("以下配置项填写错误: ")
        for err in err_info:
            logger.critical(f"{err[0].ljust(pos_maxlen)} => {err[1]}")

    app = FastAPI(docs_url=None, redoc_url=None)
    port = os.getenv("BBOT_WEBUI_PORT", 6080)

    @app.get("/api/config/load")
    async def load_config(config: dict):
        try:
            _BotConfig(**config)
        except ValueError as e:
            err = _BotConfig.valueerror_parser(e)
            valueerror_output(err)

    @app.post("/api/config/save")
    async def save_config(config: _BotConfig):
        try:
            _BotConfig.save(config)
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

    if isinstance(err, dict):
        valueerror_output(err)
    logger.critical(
        f"由于 {reason} ，导致配置加载失败, 请打开浏览器访问 BBot 主机的 http://0.0.0.0:{port} 进行配置，或手动配置完成后使用 Ctrl+C 重载配置"
    )
    uvicorn.run(app, host="0.0.0.0", port=int(port))


if __name__ == "__main__":
    for _ in range(3):
        try:
            BotConfig = _BotConfig.load(allow_create=True)
            BotConfig.save()
            break
        except ValueError as e:
            load_config_webui(reason="配置文件填写错误", err=_BotConfig.valueerror_parser(e))
        except FileNotFoundError:
            load_config_webui(reason="配置文件不存在")
        except Exception as e:
            logger.exception(e)
            load_config_webui(reason="未知原因")
    else:
        logger.critical("配置加载失败超过 3 次, 请检查配置文件后重新启动")
        sys.exit(1)

    import bot  # noqa
