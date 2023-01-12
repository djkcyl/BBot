import json
import yaml

from pathlib import Path
from loguru import logger
from typing import Optional
from pydantic import AnyHttpUrl, BaseModel, Extra, validator

DEFUALT_CONFIG_PATH = Path("data", "bot_config.yaml")


class _Mirai(BaseModel, extra=Extra.ignore):
    account: int
    verify_key: str = "mah"
    mirai_host: AnyHttpUrl = AnyHttpUrl("http://bbot-mah:6081", scheme="http")


class _Debug(BaseModel, extra=Extra.ignore):
    groups: Optional[list[int]] = [123]
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
            logger.warning("debug.groups 为空或格式不为 list, 已重置为 None")

    # 验证是否可以开启 debug
    @validator("enable")
    def can_use_login(cls, enable, values):
        if not enable:
            return enable
        logger.info("已检测到开启Debug模式")
        try:
            if values["groups"]:
                return enable
            raise KeyError
        except KeyError as key_err:
            raise ValueError("已启用 debug 但未填入合法的群号") from key_err


class _Bilibili(BaseModel, extra=Extra.ignore):
    username: Optional[int]
    password: Optional[str]
    use_login: bool = False
    mobile_style: bool = True
    concurrency: int = 5

    # 验证是否可以登录
    @validator("use_login", always=True)
    def can_use_login(cls, use_login, values):
        if not use_login:
            return use_login
        logger.info("已检测到开启BiliBili登录模式")
        try:
            if isinstance(values["username"], int) and isinstance(values["password"], str):
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


class _Event(BaseModel, extra=Extra.ignore):
    mute: bool = True
    permchange: bool = True
    push: bool = True
    subscribe: bool = True


class _Webui(BaseModel, extra=Extra.ignore):
    webui_host: str = "0.0.0.0"
    webui_port: int = 6080
    webui_enable: bool = False


class _BotConfig(BaseModel, extra=Extra.ignore):
    Mirai: _Mirai
    Debug: _Debug
    Bilibili: _Bilibili
    Event: _Event
    Webui: _Webui
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

    # 从模板创建配置文件
    @staticmethod
    def _create_file(file: Path = DEFUALT_CONFIG_PATH):
        if not file.parent.exists():
            logger.warning("配置文件目录不存在，已自动创建")
            file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(
            Path(__file__)
            .parent.parent.joinpath("static")
            .joinpath("bot_config.exp.yaml")
            .read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    # 读取配置文件
    @staticmethod
    def _read_file(file: Path = DEFUALT_CONFIG_PATH):
        bot_config: dict = yaml.load(file.read_bytes(), Loader=yaml.FullLoader)
        # 兼容旧配置, 将配置文件中的小写的配置项转为大写
        for old_config in ["mirai", "debug", "bilibili", "event"]:
            if old_config in bot_config:
                logger.warning(f"检测到旧版配置项, 转化为新版配置项: {old_config} => {old_config.capitalize()}")
                bot_config[old_config.capitalize()] = bot_config[old_config]
                del bot_config[old_config]
        return bot_config

    # ValueError解析
    @staticmethod
    def valueerror_parser(e: ValueError):
        return {
            ".".join([str(x) for x in err["loc"]]): err["msg"] for err in json.loads(e.json())
        }

    # 从配置文件中加载配置
    @classmethod
    def load(cls, file: Path = DEFUALT_CONFIG_PATH, allow_create: bool = False):
        # 如果文件不存在
        if not file.exists():
            if allow_create:
                cls._create_file(file)
            else:
                raise FileNotFoundError
        return cls.parse_obj(cls._read_file())

    # 将配置保存至文件中
    def save(self, file: Path = DEFUALT_CONFIG_PATH, allow_create: bool = False):
        class NoAliasDumper(yaml.SafeDumper):
            def ignore_aliases(self, data):
                return True

        # 如果文件不存在
        if not file.exists():
            if allow_create:
                self._create_file(file)
            else:
                raise FileNotFoundError
        # 写入文件
        file.write_text(
            yaml.dump(json.loads(self.json()), Dumper=NoAliasDumper, sort_keys=False),
            encoding="utf-8",
        )


BotConfig: _BotConfig = _BotConfig.load(allow_create=True)
