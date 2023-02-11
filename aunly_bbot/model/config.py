import json
import yaml
import click

from pathlib import Path
from typing import Optional, Literal
from pydantic import AnyHttpUrl, BaseModel, Extra, validator, ValidationError

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
            click.secho("groups 格式为 int, 已重置为 list[groups]", fg="bright_yellow")
            return [groups]
        elif type(groups) == list:
            return groups
        else:
            click.secho("debug.groups 为空或格式不为 list, 已重置为 None", fg="bright_yellow")

    # 验证是否可以开启 debug
    @validator("enable")
    def can_use_login(cls, enable, values):
        if not enable:
            return enable
        click.secho("已检测到开启 Debug 模式", fg="bright_yellow")
        try:
            if values["groups"]:
                return enable
            raise KeyError
        except KeyError as key_err:
            raise ValueError("已启用 Debug 但未填入合法的群号") from key_err


class _Bilibili(BaseModel, extra=Extra.ignore):
    username: Optional[int]
    password: Optional[str]
    use_login: bool = False
    mobile_style: bool = True
    concurrency: int = 5
    dynamic_font: Optional[str] = "HarmonyOS_Sans_SC_Medium.woff2"
    dynamic_font_source: Optional[Literal["local", "remote", "system"]] = "local"

    # 验证是否可以登录
    @validator("use_login", always=True)
    def can_use_login(cls, use_login, values):
        if not use_login:
            return use_login
        click.secho("已检测到开启 BiliBili 登录模式，不推荐使用", fg="bright_yellow", bold=True)
        try:
            if isinstance(values["username"], int) and isinstance(values["password"], str):
                return use_login
        except KeyError as key_err:
            raise ValueError("已启用登录但未填入合法的用户名与密码") from key_err

    # 验证 Bilibili gRPC 并发数
    @validator("concurrency")
    def limit_concurrency(cls, concurrency):
        if concurrency > 50:
            click.secho("gRPC 并发数超过 50，已自动调整为 50", fg="bright_yellow")
            return 50
        elif concurrency < 1:
            click.secho("gRPC 并发数小于 1，已自动调整为 1", fg="bright_yellow")
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
    update_check: bool = True

    # 验证 admins 列表
    @validator("admins")
    def verify_admins(cls, admins, values):
        if type(admins) == int:
            click.secho("admins 格式为 int, 已重置为 list[admins]", fg="bright_yellow")
            admins = [admins]
        elif type(admins) != list or not admins:
            if "master" not in values:
                raise ValueError("未查询到合法的 master")
            click.secho("admins 为空或格式不为 list, 已重置为 list[master]", fg="bright_yellow")
            return [values["master"]]
        try:
            if "master" not in values:
                return admins
            if values["master"] in admins:
                return admins
        except KeyError:
            click.secho("admins 内未包含 master 账号, 已自动添加", fg="bright_yellow")
            return admins.append(values["master"])

    # 读取配置文件
    @staticmethod
    def _read_file(file: Path = DEFUALT_CONFIG_PATH):
        bot_config: dict = yaml.load(file.read_bytes(), Loader=yaml.FullLoader)
        # 兼容旧配置, 将配置文件中的小写的配置项转为大写
        for old_config in ["mirai", "debug", "bilibili", "event"]:
            if old_config in bot_config:
                click.secho(
                    f"检测到旧版配置项, 转化为新版配置项: {old_config} => {old_config.capitalize()}",
                    fg="bright_yellow",
                )
                bot_config[old_config.capitalize()] = bot_config[old_config]
                del bot_config[old_config]
        return bot_config

    # ValueError解析
    @staticmethod
    def valueerror_parser(e: ValidationError):
        return {
            ".".join([str(x) for x in err["loc"]]): err["msg"] for err in json.loads(e.json())
        }

    # 从配置文件中加载配置
    @classmethod
    def load(cls, file: Path = DEFUALT_CONFIG_PATH):
        # 如果文件不存在
        if not file.exists():
            raise FileNotFoundError
        return cls.parse_obj(cls._read_file())

    # 将配置保存至文件中
    def save(self, file: Path = DEFUALT_CONFIG_PATH):
        class NoAliasDumper(yaml.SafeDumper):
            def ignore_aliases(self, data):
                return True

        # 写入文件
        file.write_text(
            yaml.dump(json.loads(self.json()), Dumper=NoAliasDumper, sort_keys=False),
            encoding="utf-8",
        )
