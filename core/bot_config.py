import yaml

from pathlib import Path
from loguru import logger
from pydantic import AnyHttpUrl


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


bot_config_file = Path("data/bot_config.yaml")
if bot_config_file.exists():
    bot_config = yaml.load(bot_config_file.read_bytes(), Loader=yaml.FullLoader)
else:
    logger.error("未找到配置文件，请检查配置文件（data/bot_group.yaml）是否存在")
    exit()

if bot_config["master"] not in bot_config["admins"]:
    logger.warning("管理员内未添加主人，已自动添加")
    bot_config["admins"].append(bot_config["master"])


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


def save_config():
    bot_config_file.write_text(yaml.dump(bot_config, Dumper=NoAliasDumper))
