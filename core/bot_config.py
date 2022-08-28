import json
import sys
from pathlib import Path
from typing import Optional, Union

import yaml
from loguru import logger
from pydantic import AnyHttpUrl, BaseSettings, validator, Field

# 数据模型类

class _Mirai(BaseSettings):
    account    : int
    verify_key : str
    mirai_host : AnyHttpUrl

class _Debug(BaseSettings):
    groups : Optional[list[int]]
    enable : bool = False

    # 规范 groups 内容
    @validator('groups')
    def specification_groups(cls, groups):
        # 若 groups 为 int, 转换为 [admins]
        if type(groups) == int:
            logger.warning(f'groups 格式为 int, 已重置为 list[groups]')
            return [groups]
        # 若 groups 为 list, 不转换
        elif type(groups) == list:
            return groups
        # 其他情况, 转换为 [None]
        else:
            logger.warning(f'debug.groups 为空或格式不为 list, 已重置为 list[None]')
            return [None]

    # 验证是否可以开启 debug
    @validator('enable')
    def can_use_login(cls, enable, values):
        # 如果未启用 debug
        if not enable:
            return enable
        # 如果启用 debug，检查 groups 是否存在
        # 若存在则启用 debug
        try:
            if values['groups']:
                return enable
            raise KeyError
        # 若不存在则抛出 ValueError
        except KeyError:
            raise ValueError(f'已启用 debug 但未填入合法的群号')


class _Bilibili(BaseSettings):
    username     : Optional[int]
    password     : Optional[str]
    mobile_style : bool = True
    concurrency  : int  = 5
    use_login    : bool = False

    # 验证是否可以登录
    @validator('use_login',always=True)
    def can_use_login(cls, use_login, values):
        # 如果未启用登录
        if not use_login:
            return use_login
        # 如果启用登录，检查 username 和 password 是否存在
        # 若存在则启用登录
        try:
            if values['username'] and values['password']:
                return use_login
        # 若不存在则抛出 ValueError
        except KeyError:
            raise ValueError(f'已启用登录但未填入合法的用户名与密码')
    
    # 验证 Bilibili gRPC 并发数
    @validator('concurrency')
    def limit_concurrency(cls, concurrency, values):
        if concurrency > 50:
            logger.warning(f"gRPC 并发数超过 50，已自动调整为 50")
            return 50
        elif concurrency < 1:
            logger.warning(f"gRPC 并发数小于 1，已自动调整为 1")
            return 1
        else:
            return concurrency

class _Event(BaseSettings):
    mute       : bool = True
    permchange : bool = True

class _BotConfig(BaseSettings):
    Mirai    : _Mirai
    Debug    : _Debug
    Bilibili : _Bilibili
    Event    : _Event
    log_level      : str  = 'INFO'
    name           : str  = 'BBot'
    master         : int  = 123
    admins         : Optional[Union[list[int],int]]
    access_control : bool = True

    # 验证 admins 列表
    @validator('admins')
    def verify_admins(cls, admins, values):
        # 若 admins 为 int, 转化为 [admins]
        if type(admins) == int:
            logger.warning(f'admins 格式为 int, 已重置为 list[admins]')
            admins = [admins]
        # 若 admins 既不是 int 也不是 list, 或为空 list，转化为 [master]
        elif (type(admins) != list) or (not admins):
            logger.warning(f'admins 为空或格式不为 list, 已重置为 list[master]')
            return [values['master']]
        # 验证 admins 是否内含 master
        try:
            if values['master'] in admins:
                return admins
        except KeyError:
            logger.warning(f'admins 内未包含 master 账号, 已自动添加')
            return admins.append(values['master'])
        

# 保存文件
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

def save_config():
    bot_config_file.write_text(
        yaml.dump(json.loads(BotConfig.json()), Dumper=NoAliasDumper, sort_keys=False)
    )

# 读取配置
## 设定路径
bot_config_file = Path("data").joinpath("bot_config.yaml")
bot_config_file.parent.mkdir(parents=True, exist_ok=True)
## 尝试读取配置项文件
if bot_config_file.exists():
    bot_config:dict = yaml.load(bot_config_file.read_bytes(), Loader=yaml.FullLoader)
    ## 兼容旧配置, 将配置文件中的小写的配置项转为大写
    for old_config in ['mirai','debug','bilibili','event']:
        if old_config in bot_config.keys():
            logger.warning(f'检测到旧版配置项, 转化为新版配置项: {old_config} => {old_config.capitalize()}')
            bot_config[old_config.capitalize()] = bot_config[old_config]
            del bot_config[old_config]
## 未能读取到配置文件，新建配置文件
elif Path(sys.argv[0]).name != "_child.py":
    logger.error(f"未找到配置文件，已为您创建默认配置文件（{bot_config_file}），请修改后重新启动")
    bot_config_file.write_text(
        Path(__file__)
        .parent.parent.joinpath("data")
        .joinpath("bot_config.exp.yaml")
        .read_text()
    )
    sys.exit(1)
## 以配置项文件生成BotConfig，并保存
BotConfig = _BotConfig.parse_obj(bot_config)
save_config()
    
