import click


@click.group()
def main():
    pass


@click.command()
def run():
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
