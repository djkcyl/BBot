import click

from pathlib import Path


@click.group()
def main():
    pass


@click.command()
def run():
    if not Path("data", "bot_config.yaml").exists():
        click.secho("未找到配置文件，请先使用 bbot config 命令进行配置。", fg="red", bold=True)
        return

    from .run import run_bot

    run_bot()


@click.command()
def config():

    from .config import click_config

    click_config()


main.add_command(run)
main.add_command(config)

main.commands["run"].help = "运行 BBot"
main.commands["config"].help = "BBot 配置向导"
