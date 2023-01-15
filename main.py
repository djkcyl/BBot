import sys
import psutil

from pathlib import Path

from aunly_bbot.utils.detect_package import is_package

if is_package:
    s = psutil.Process().parent().parent()
    if s.name() == "explorer.exe":
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
        print("按回车键退出")
        input("Press Enter to exit")

        sys.exit(1)


if __name__ == "__main__":
    from aunly_bbot.cli.run import run_bot

    run_bot()
