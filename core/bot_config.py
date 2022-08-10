import sys
import yaml

from pathlib import Path
from loguru import logger
from pydantic import AnyHttpUrl


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def save_config():
    bot_config_file.write_text(
        yaml.dump(bot_config, Dumper=NoAliasDumper, sort_keys=False)
    )


bot_config_file = Path("data").joinpath("bot_config.yaml")
bot_config_file.parent.mkdir(parents=True, exist_ok=True)
if bot_config_file.exists():
    bot_config = yaml.load(bot_config_file.read_bytes(), Loader=yaml.FullLoader)
    if bot_config["master"] not in bot_config["admins"]:
        logger.warning("管理员内未添加主人，已自动添加")
        bot_config["admins"].append(bot_config["master"])
elif Path(sys.argv[0]).name != "_child.py":
    logger.error(f"未找到配置文件，已为您创建默认配置文件（{bot_config_file}），请修改后重新启动")
    bot_config_file.write_text(
        Path(__file__)
        .parent.parent.joinpath("data")
        .joinpath("bot_config.exp.yaml")
        .read_text()
    )
    sys.exit(1)


class BotConfig:
    class Mirai:
        account: int = bot_config["mirai"]["account"]
        verify_key: str = bot_config["mirai"]["verify_key"]
        mirai_host: AnyHttpUrl = bot_config["mirai"]["mirai_host"]

    class Debug:
        enable: bool = bot_config["debug"]["enable"]
        groups: list[int] = bot_config["debug"]["groups"]

    class Bilibili:
        username: int = bot_config["bilibili"]["username"]
        password: str = bot_config["bilibili"]["password"]
        mobile_style: bool = bot_config["bilibili"]["mobile_style"]

    class Event:
        mute: bool = bot_config["event"]["mute"]
        permchange: bool = bot_config["event"]["permchange"]

    name: str = bot_config["name"]
    master: int = bot_config["master"]
    admins: list[int] = bot_config["admins"]
    access_control: bool = bot_config["access_control"]


def open_access_control():
    if bot_config["access_control"]:
        return False
    bot_config["access_control"] = True
    save_config()
    return True


def close_access_control():
    if bot_config["access_control"]:
        bot_config["access_control"] = False
        save_config()
        return True
    return False


def add_admin(admin: int):
    if admin in bot_config["admins"]:
        return False
    bot_config["admins"].append(admin)
    bot_config_file.write_text(yaml.dump(bot_config, Dumper=NoAliasDumper))
    return True


def remove_admin(admin: int):
    if admin in bot_config["admins"]:
        bot_config["admins"].remove(admin)
        bot_config_file.write_text(yaml.dump(bot_config, Dumper=NoAliasDumper))
        return True
    return False
