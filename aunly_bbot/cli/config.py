import sys
import click
import httpx

from yarl import URL
from pathlib import Path
from json import JSONDecodeError
from noneprompt import (
    Choice,
    ListPrompt,
    InputPrompt,
    ConfirmPrompt,
    CancelledError,
    CheckboxPrompt,
)

from ..model.config import _BotConfig
from ..core.announcement import BBOT_ASCII_LOGO


data = {}


class CliConfig:
    config: dict = {
        "Mirai": {},
        "Debug": {},
        "Bilibili": {},
        "Webui": {},
    }
    __session: str = ""

    def __init__(self) -> None:
        self.mirai_mirai_host()
        self.mirai_verify_key()
        self.debug()
        self.bilibili_mobile_style()
        self.bilibili_concurrent()
        self.event()
        self.webui()
        self.log_level()
        self.name()
        self.access_control()
        self.master()
        self.admins()
        self.max_subscriptions()
        self.update_check()

        if data.get("session", None):
            httpx.post(
                f"{self.config['Mirai']['mirai_host']}/release",
                json={
                    "sessionKey": self.__session,
                    "qq": self.config["Mirai"]["account"],
                },
            )

    # ----- utils -----
    @staticmethod
    def is_qq(qq: str) -> bool:
        """判断是否为合法的 QQ 号"""
        return len(qq) >= 5 and len(qq) <= 17 if qq.isdigit() else False

    def verify_friend(self, qq: str) -> bool:
        """验证是否为好友"""
        friend_list = httpx.get(
            f"{self.config['Mirai']['mirai_host']}/friendList",
            params={"sessionKey": self.__session},
        ).json()["data"]
        return any(friend["id"] == int(qq) for friend in friend_list)

    def mirai_account(self):
        while True:
            mirai_account = InputPrompt("请输入你已经登录 Mirai 的 QQ 账号: ").prompt()
            if self.is_qq(mirai_account):
                self.config["Mirai"]["account"] = int(mirai_account)
                return
            click.secho("输入的 QQ 号不合法！", fg="bright_red", bold=True)

    # ----- Mirai -----
    def mirai_mirai_host(self):
        while True:
            mirai_host = InputPrompt(
                "请输入 Mirai HTTP API 的地址: ", "http://localhost:8080"
            ).prompt()
            try:
                if not URL(mirai_host).is_absolute():
                    raise ValueError("输入的地址不合法！")
            except Exception:
                click.secho("输入的地址不合法！", fg="bright_red", bold=True)
                continue

            try:
                if httpx.get(f"{mirai_host}/about").json()["data"]["version"] < "2.6.1":
                    click.secho(
                        "Mirai HTTP API 版本低于 2.6.1，可能会导致部分功能无法使用！请升级至最新版",
                        fg="bright_red",
                        bold=True,
                    )
                self.config["Mirai"]["mirai_host"] = mirai_host
                return
            except httpx.HTTPError:
                click.secho("无法连接到 Mirai HTTP API，请检查地址是否正确！", fg="bright_red", bold=True)
                continue

    def mirai_verify_key(self):
        while True:
            mirai_key: str = InputPrompt(
                "请输入 Mirai HTTP API 的 verifyKey: ", is_password=True
            ).prompt()
            try:
                # check verifyKey
                verify = httpx.post(
                    f"{self.config['Mirai']['mirai_host']}/verify",
                    json={"verifyKey": mirai_key},
                ).json()
                if verify["code"] != 0:
                    click.secho("Mirai HTTP API 的 verifyKey 错误！", fg="bright_red", bold=True)
                    continue
                self.__session = verify["session"]

                # check bind
                while True:
                    self.mirai_account()
                    bind = httpx.post(
                        f"{self.config['Mirai']['mirai_host']}/bind",
                        json={
                            "sessionKey": self.__session,
                            "qq": self.config["Mirai"]["account"],
                        },
                    ).json()
                    if bind["code"] == 0 and (
                        httpx.get(
                            f"{self.config['Mirai']['mirai_host']}/sessionInfo",
                            params={"sessionKey": self.__session},
                        ).json()["code"]
                        == 0
                    ):
                        break
                    click.secho(
                        f"Mirai HTTP API 验证错误（可能是QQ号填写错误）：{bind['msg']}！",
                        fg="bright_red",
                        bold=True,
                    )

                # all clear
                click.secho("Mirai HTTP API 验证成功！", fg="bright_green", bold=True)
                self.config["Mirai"]["verify_key"] = mirai_key
                return

            except httpx.HTTPError:
                click.secho("无法连接到 Mirai HTTP API，请检查地址是否正确！", fg="bright_red", bold=True)
                self.mirai_mirai_host()
            except JSONDecodeError:
                click.secho("输入的地址不为 Mirai HTTP API 的地址！", fg="bright_red", bold=True)
                self.mirai_mirai_host()

    def debug(self):
        debug = ListPrompt(
            "是否开启调试模式？（开启后 Bot 将只会响应调试群的消息）",
            [Choice("是（开启）"), Choice("否（关闭）")],
            allow_filter=False,
            default_select=1,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        if debug.name == "是（开启）":
            self.config["Debug"]["enable"] = True
            self.debug_group()
        else:
            self.config["Debug"] = {"enable": False, "groups": [123456789]}

    def debug_group(self):
        self.config["Debug"]["groups"] = []
        while True:
            debug_group = InputPrompt("请输入调试群的群号（输入 n 停止）: ").prompt()
            if debug_group.lower() == "n":
                if not self.config["Debug"]["groups"]:
                    click.secho("请至少输入一个群号！", fg="bright_red", bold=True)
                    continue
                return
            if not debug_group.isdigit():
                click.secho("输入的群号不合法！", fg="bright_red", bold=True)
                continue
            if int(debug_group) in self.config["Debug"]["groups"]:
                click.secho("该群已在调试群列表中，请重新输入！", fg="bright_red", bold=True)
                continue
            debug_group = int(debug_group)
            group_list = httpx.get(
                f"{self.config['Mirai']['mirai_host']}/groupList",
                params={"sessionKey": self.__session},
            ).json()["data"]

            for group in group_list:
                if group["id"] == debug_group:
                    self.config["Debug"]["groups"].append(debug_group)
                    break
            else:
                click.secho("Bot 未加入该群，请重新输入！", fg="bright_red", bold=True)

    def bilibili_mobile_style(self):
        mobile_style = ListPrompt(
            "是否使用手机端样式？",
            [Choice("是（开启）"), Choice("否（关闭）")],
            allow_filter=False,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        self.config["Bilibili"]["mobile_style"] = mobile_style.name == "是（开启）"

    def bilibili_concurrent(self):
        while True:
            concurrent = InputPrompt("请输入并发数（理论该值越大推送效率越高）: ", default_text="10").prompt()
            if concurrent.isdigit() and 50 >= int(concurrent) > 0:
                self.config["Bilibili"]["concurrency"] = int(concurrent)
                return
            click.secho("输入的并发数不合法！请输入 1 - 50 之间的整数", fg="bright_red", bold=True)

    def event(self):
        event_map = {"禁言": "mute", "权限变更": "permission", "动态推送": "push", "UP 订阅": "subscribe"}
        event_list = CheckboxPrompt(
            "请选择需要私聊管理员推送的事件",
            [Choice("禁言"), Choice("权限变更"), Choice("动态推送"), Choice("UP 订阅")],
            default_select=[0, 1, 2, 3],
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按空格开关, 按回车确认",
        ).prompt()
        self.config["Event"] = {event_map[event.name]: True for event in event_list}

    def webui(self):
        webui = ListPrompt(
            "是否开启 WebUI？",
            [Choice("是（开启）"), Choice("否（关闭）")],
            allow_filter=False,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        if webui.name == "是（开启）":
            self.webui_data()
        else:
            self.config["Webui"] = {
                "webui_host": "0.0.0.0",
                "webui_port": 6080,
                "webui_enable": False,
            }

    def webui_data(self):
        while True:
            webui_url = InputPrompt(
                "请输入 WebUI 的地址: ", default_text="http://0.0.0.0:6080"
            ).prompt()
            try:
                url = URL(webui_url)
                if not url.is_absolute():
                    raise ValueError("输入的地址不合法！")
            except Exception:
                click.secho("输入的地址不合法！", fg="bright_red", bold=True)
                continue
            self.config["Webui"] = {
                "webui_host": url.host,
                "webui_port": url.port,
                "webui_enable": True,
            }
            return

    # ----- Other -----
    def master(self):
        while True:
            master = InputPrompt("请输入你的 QQ 号（作为最高管理员账号）: ").prompt()
            if not self.is_qq(master):
                click.secho("输入的 QQ 号不合法！", fg="bright_red", bold=True)
                continue

            if self.verify_friend(master):
                self.config["master"] = int(master)
                return
            else:
                click.secho("你输入的 QQ 号不是 Bot 的好友！", fg="bright_red", bold=True)

    def admins(self):
        self.config["admins"] = [self.config["master"]]
        while True:
            admin = InputPrompt("请输入其他管理员的 QQ 号（输入 n 停止）: ").prompt()
            if admin.lower() == "n" or admin == "":
                return
            if not self.is_qq(admin):
                click.secho("输入的 QQ 号不合法！", fg="bright_red", bold=True)
                continue
            if int(admin) in self.config["admins"]:
                click.secho("该 QQ 号已经在管理员列表中了！", fg="bright_red", bold=True)
                continue
            if not self.verify_friend(admin):
                click.secho("该 QQ 号不是 Bot 的好友！", fg="bright_red", bold=True)
                continue

            self.config["admins"].append(int(admin))

    def log_level(self):
        self.config["log_level"] = (
            ListPrompt(
                "请选择日志等级",
                [
                    Choice("DEBUG"),
                    Choice("INFO"),
                    Choice("WARNING"),
                ],
                allow_filter=False,
                default_select=1,
                annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
            )
            .prompt()
            .name
        )

    def name(self):
        while True:
            bot_name = InputPrompt("请输入 Bot 的昵称: ", default_text="BBot").prompt()
            if 0 < len(bot_name) <= 16:
                self.config["name"] = bot_name
                return
            click.secho("输入的昵称不合法（请输入 1 - 16 位字符）", fg="bright_red", bold=True)

    def max_subscriptions(self):
        while True:
            max_subscriptions = InputPrompt("请输入每个群的最大订阅数: ", default_text="4").prompt()
            if max_subscriptions.isdigit() and 0 < int(max_subscriptions) <= 100:
                self.config["max_subsubscribe"] = int(max_subscriptions)
                return
            click.secho("输入的订阅数不合法！请输入 1 - 100 之间的整数", fg="bright_red", bold=True)

    def access_control(self):
        access_control = ListPrompt(
            "是否开启白名单控制？（仅允许加入白名单中的群）",
            [Choice("是（开启）"), Choice("否（关闭）")],
            allow_filter=False,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        self.config["access_control"] = access_control.name == "是（开启）"

    def update_check(self):
        update_check = ListPrompt(
            "是否开启更新检查？",
            [Choice("是（开启）"), Choice("否（关闭）")],
            allow_filter=False,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        self.config["update_check"] = update_check.name == "是（开启）"


def click_config(ignore_exist=False):
    click.secho(BBOT_ASCII_LOGO, fg="bright_blue", bold=True)
    click.secho("\n欢迎使用 BBot 配置向导！\n", fg="bright_green", bold=True)
    click.secho("请按照提示输入相关信息后，按回车确认\n", fg="bright_yellow")

    try:
        _config(ignore_exist)
        sys.exit(0)
    except CancelledError:
        click.secho("配置向导已取消。", fg="bright_yellow", bold=True)
        sys.exit(0)


def _config(ignore_exist):
    if list(Path(".").iterdir()) and not ignore_exist:
        click.secho("当前目录不为空，可能会导致未知的错误。", fg="bright_yellow", bold=True)
        click.secho("请确保当前目录没有 Bot 之外的文件。", fg="bright_yellow", bold=True)

        if not ConfirmPrompt("是否仍要继续配置流程？", default_choice=False).prompt():
            sys.exit(0)
        if Path("data", "bot_config.yaml").exists():
            click.secho("检测到已存在的配置文件，将覆盖原配置。", fg="bright_yellow", bold=True)
            if not ConfirmPrompt("是否仍要继续配置流程？", default_choice=False).prompt():
                sys.exit(0)

    if not Path("data").exists():
        click.secho("data 目录不存在，已自动创建", fg="bright_yellow")
        Path("data").mkdir(parents=True, exist_ok=True)

    click.secho("正在进入配置流程……", fg="bright_green", bold=True)
    _BotConfig.parse_obj(CliConfig().config).save()

    click.secho("恭喜你，配置已完成！", fg="bright_green", bold=True)
    click.secho("现在，你可以使用 bbot run 命令运行 BBot 了。", fg="bright_blue", bold=True)
