import click
from ..core.announcement import PROJECT_VERSION


@click.group(help="BBot 命令行工具")
@click.version_option(
    PROJECT_VERSION,
    "-v",
    "--version",
    package_name="aunly-bbot",
    prog_name="BBot",
    message="%(prog)s 当前版本：%(version)s",
    help="显示 BBot 版本",
)
@click.help_option("-h", "--help", help="显示帮助信息")
def main():
    pass


@click.command(name="run", help="运行 BBot")
@click.option("-t", "--test", is_flag=True, help="测试模式")
@click.help_option("-h", "--help", help="显示帮助信息")
def run_bot(test: bool):
    if test:
        from ..core import cache

        cache["test"] = True

    from .run import run_bot

    run_bot()


@click.command(name="api", help="运行 BBot Playwright 截图 API 服务")
@click.help_option("-h", "--help", help="显示帮助信息")
def run_api():
    import uvicorn
    from .api import app

    uvicorn.run(app, host="0.0.0.0", port=9000)


@click.command(help="BBot 配置向导")
def config():
    from .config import click_config

    click_config()


main.add_command(run_bot)
main.add_command(run_api)
main.add_command(config)
