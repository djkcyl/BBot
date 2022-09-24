import os
import sys
import psutil
import sentry_sdk

from pathlib import Path

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
import bot
