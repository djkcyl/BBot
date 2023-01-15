import click

from pydantic import ValidationError

from ..model.config import _BotConfig


def valueerror_output(err: dict):
    err_info = []
    pos_maxlen = 0
    for err_pos, err_msg in err.items():
        pos_maxlen = max(pos_maxlen, len(err_pos))
        err_info.append([err_pos, err_msg])
    click.secho("以下配置项填写错误: ", fg="bright_red")
    for err in err_info:
        click.secho(f"{err[0].ljust(pos_maxlen)} => {err[1]}", fg="bright_red")


while True:
    try:
        BotConfig: _BotConfig = _BotConfig.load()
        break
    except ValidationError as e:
        valueerror_output(_BotConfig.valueerror_parser(e))
    except FileNotFoundError:
        click.secho("未找到配置文件, 正在进入配置流程......", fg="bright_red", bold=True)
    except Exception as e:
        click.secho(f"未知错误: {e}", fg="bright_red", bold=True)

    from ..cli.config import click_config

    click_config()
