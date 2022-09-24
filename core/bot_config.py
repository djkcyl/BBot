import sys
import json
import yaml

from pathlib import Path
from loguru import logger
from typing import Optional
from sentry_sdk import capture_exception
from pydantic import AnyHttpUrl, BaseSettings, Extra, validator

# 数据模型类


class _Mirai(BaseSettings, extra=Extra.ignore):
    account: int
    verify_key: str
    mirai_host: AnyHttpUrl


class _Debug(BaseSettings, extra=Extra.ignore):
    groups: Optional[list[int]]
    enable: bool = False

    # 规范 groups 内容
    @validator("groups")
    def specification_groups(cls, groups):
        if type(groups) == int:
            logger.warning("groups 格式为 int, 已重置为 list[groups]")
            return [groups]
        elif type(groups) == list:
            return groups
        else:
            logger.warning("debug.groups 为空或格式不为 list, 已重置为 list[None]")
            return [None]

    # 验证是否可以开启 debug
    @validator("enable")
    def can_use_login(cls, enable, values):
        if not enable:
            return enable
        try:
            if values["groups"]:
                return enable
            raise KeyError
        except KeyError as key_err:
            raise ValueError("已启用 debug 但未填入合法的群号") from key_err


class _Bilibili(BaseSettings, extra=Extra.ignore):
    username: Optional[int]
    password: Optional[str]
    mobile_style: bool = True
    concurrency: int = 5
    use_login: bool = False
    use_browser: bool = True

    # 验证是否可以登录
    @validator("use_login", always=True)
    def can_use_login(cls, use_login, values):
        if not use_login:
            return use_login
        try:
            if values["username"] and values["password"]:
                return use_login
        except KeyError as key_err:
            raise ValueError("已启用登录但未填入合法的用户名与密码") from key_err

    # 验证 Bilibili gRPC 并发数
    @validator("concurrency")
    def limit_concurrency(cls, concurrency):
        if concurrency > 50:
            logger.warning("gRPC 并发数超过 50，已自动调整为 50")
            return 50
        elif concurrency < 1:
            logger.warning("gRPC 并发数小于 1，已自动调整为 1")
            return 1
        else:
            return concurrency


class _Event(BaseSettings, extra=Extra.ignore):
    mute: bool = True
    permchange: bool = True


class _BotConfig(BaseSettings, extra=Extra.ignore):
    Mirai: _Mirai
    Debug: _Debug
    Bilibili: _Bilibili
    Event: _Event
    log_level: str = "INFO"
    name: str = "BBot"
    master: int = 123
    admins: Optional[list[int]]
    max_subsubscribe: int = 4
    access_control: bool = True

    # 验证 admins 列表
    @validator("admins")
    def verify_admins(cls, admins, values):
        if type(admins) == int:
            logger.warning("admins 格式为 int, 已重置为 list[admins]")
            admins = [admins]
        elif type(admins) != list or not admins:
            if "master" not in values:
                raise ValueError("未查询到合法的 master")
            logger.warning("admins 为空或格式不为 list, 已重置为 list[master]")
            return [values["master"]]
        try:
            if "master" not in values:
                return admins
            if values["master"] in admins:
                return admins
        except KeyError:
            logger.warning("admins 内未包含 master 账号, 已自动添加")
            return admins.append(values["master"])


# 保存文件
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def save_config():
    bot_config_file.write_text(
        yaml.dump(json.loads(BotConfig.json()), Dumper=NoAliasDumper, sort_keys=False),
        encoding="utf-8",
    )


# 读取配置
# 设定路径
bot_config_file = Path("data").joinpath("bot_config.yaml")
bot_config_file.parent.mkdir(parents=True, exist_ok=True)
# 尝试读取配置项文件
if bot_config_file.exists():
    bot_config: dict = yaml.load(bot_config_file.read_bytes(), Loader=yaml.FullLoader)
    # 兼容旧配置, 将配置文件中的小写的配置项转为大写
    for old_config in ["mirai", "debug", "bilibili", "event"]:
        if old_config in bot_config:
            logger.warning(f"检测到旧版配置项, 转化为新版配置项: {old_config} => {old_config.capitalize()}")
            bot_config[old_config.capitalize()] = bot_config[old_config]
            del bot_config[old_config]
    # 以配置项文件生成 BotConfig，并保存
    try:
        BotConfig = _BotConfig.parse_obj(bot_config)
    # 常见的由 Pydantic 找出的错误
    except ValueError as e:
        err_info = []
        pos_maxlen = 0
        for err in json.loads(e.json()):
            err_pos = ".".join([str(x) for x in err["loc"]])
            err_msg = err["msg"]
            pos_maxlen = max(pos_maxlen, len(err_pos))
            err_info.append([err_pos, err_msg])
        logger.critical("以下配置项填写错误: ")
        for err in err_info:
            logger.critical(f"{err[0].ljust(pos_maxlen)} => {err[1]}")
        logger.critical("请检查配置文件(data/bot_group.yaml)中上述配置内容")
        sys.exit(1)
    except Exception:
        capture_exception()
        logger.exception("配置文件存在未知错误")
        logger.critical("读取配置文件时出现未知错误, 请检查配置文件是否填写正确")
        sys.exit(1)
    save_config()

elif Path(sys.argv[0]).name != "_child.py":
    logger.error(f"未找到配置文件，已为您创建默认配置文件（{bot_config_file}），请修改后重新启动")
    bot_config_file.write_text(
        Path(__file__)
        .parent.parent.joinpath("data", "bot_config.exp.yaml")
        .read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    sys.exit(1)
