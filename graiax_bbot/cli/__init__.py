import click


@click.group()
def main():
    pass


@click.command()
def run():
    from .bot import run

    run()


main.add_command(run)


main.commands["run"].help = "执行此命令运行 BBot"
