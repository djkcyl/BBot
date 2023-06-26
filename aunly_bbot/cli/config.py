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

from ..core import cache
from ..model.config import _BotConfig
from ..utils.detect_package import is_full
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
        self.skip_verify = cache.get("skip_verify", False)
        self.mirai_mirai_host()
        self.mirai_verify_key()
        self.debug()
        self.use_browser()
        self.bilibili_concurrent()
        self.openai_summary()
        self.bilibili_username()
        self.use_bilibili_login()
        self.wordcloud()
        self.bcut_asr()
        self.event()
        self.webui()
        self.log_level()
        self.name()
        self.access_control()
        self.master()
        self.admins()
        self.max_subscriptions()
        self.update_check()

        if data.get("session"):
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
            if self.skip_verify:
                self.config["Mirai"]["mirai_host"] = mirai_host
                return
            try:
                if not URL(mirai_host).is_absolute():
                    raise ValueError("输入的地址不合法！")
            except Exception:
                click.secho("输入的地址不合法！", fg="bright_red", bold=True)
                continue

            try:
                if httpx.get(f"{mirai_host}/about").json()["data"]["version"] < "2.6.1":
                    click.secho(
                        "Mirai HTTP API 版本低于 2.6.1，可能会导致部分功能无法使用！请注意及时升级至最新版",
                        fg="bright_red",
                        bold=True,
                    )
                self.config["Mirai"]["mirai_host"] = mirai_host
                return
            except (KeyError, JSONDecodeError) as e:
                click.secho(
                    f"{type(e)}\n你输入的地址可能不是 Mirai HTTP API 的地址或 Mirai HTTP API 运行异常，请检查后重试！",
                    fg="bright_red",
                    bold=True,
                )
            except httpx.HTTPError:
                click.secho("无法连接到 Mirai HTTP API，请检查地址是否正确！", fg="bright_red", bold=True)
                continue

    def mirai_verify_key(self):
        while True:
            mirai_key: str = InputPrompt(
                "请输入 Mirai HTTP API 的 verifyKey: ", is_password=True
            ).prompt()
            if self.skip_verify:
                self.config["Mirai"]["verify_key"] = mirai_key
                return
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
            except (KeyError, JSONDecodeError) as e:
                click.secho(
                    f"{type(e)}\n你输入的地址可能不是 Mirai HTTP API 的地址或 Mirai HTTP API 运行异常，请检查后重试！",
                    fg="bright_red",
                    bold=True,
                )
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
            if self.skip_verify:
                self.config["Debug"]["groups"].append(debug_group)
                return
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

    def use_browser(self):
        if is_full:
            browser = ListPrompt(
                "是否使用浏览器进行动态页面截图？",
                [Choice("是（开启）"), Choice("否（关闭）")],
                allow_filter=False,
                default_select=1,
                annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
            ).prompt()
            self.config["Bilibili"]["use_browser"] = browser.name == "是（开启）"
            self.bilibili_mobile_style()
            self.render_style()
            self.allow_fallback()
        else:
            self.config["Bilibili"]["use_browser"] = False

    def bilibili_mobile_style(self):
        if is_full:
            mobile_style = ListPrompt(
                "是否在浏览器中使用手机端样式？",
                [Choice("是（开启）"), Choice("否（关闭）")],
                allow_filter=False,
                annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
            ).prompt()
            self.config["Bilibili"]["mobile_style"] = mobile_style.name == "是（开启）"
        else:
            self.config["Bilibili"]["mobile_style"] = False

    def render_style(self):
        if is_full:
            mobile_style = ListPrompt(
                "请选择使用的视频信息渲染模板？（bbot_default无需浏览器，其他均需求浏览器）",
                [Choice("bbot_default"), Choice("style_blue")],
                allow_filter=False,
                annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
            ).prompt()
            self.config["Bilibili"]["render_style"] = mobile_style.name
        else:
            self.config["Bilibili"]["render_style"] = "bbot_default"

    def allow_fallback(self):
        allow_fallback = ListPrompt(
            "是否允许使用备用动态图片渲染（在浏览器截图失败时尝试使用）？",
            [Choice("是（开启）"), Choice("否（关闭）")],
            allow_filter=False,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        self.config["Bilibili"]["allow_fallback"] = allow_fallback.name == "是（开启）"

    def openai_summary(self):
        openai_summary = ListPrompt(
            "是否使用 OpenAI 进行视频和专栏内容摘要提取？",
            [Choice("是（开启）"), Choice("否（关闭）")],
            allow_filter=False,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        if openai_summary.name == "是（开启）":
            self.config["Bilibili"]["openai_summarization"] = True
            self.openai_api_token()
            self.openai_model()
        else:
            self.config["Bilibili"]["openai_summarization"] = False

    def openai_api_token(self):
        openai_token = InputPrompt("请输入 OpenAI Token: ").prompt()
        if len(openai_token) != 51:
            click.secho("输入的 OpenAI Token 不合法（长度应为 51 位）", fg="bright_red", bold=True)
            self.openai_api_token()
        if openai_token.startswith("sk-"):
            self.config["Bilibili"]["openai_api_token"] = openai_token
        else:
            click.secho("输入的 OpenAI Token 不合法（应以 sk- 开头）", fg="bright_red", bold=True)
            self.openai_api_token()

    def openai_model(self):
        openai_model = ListPrompt(
            "请选择 OpenAI 模型",
            [
                Choice("gpt-3.5-turbo-0613"),
                Choice("gpt-3.5-turbo-16k-0613"),
                Choice("gpt-4-0613"),
            ],
            allow_filter=False,
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()
        self.config["Bilibili"]["openai_model"] = openai_model.name

    def openai_proxy(self):
        if openai_proxy_url := InputPrompt("请输入 OpenAI 代理地址（留空则不使用代理）: ").prompt():
            if not URL(openai_proxy_url).is_absolute():
                click.secho("输入的 OpenAI 代理地址不合法！", fg="bright_red", bold=True)
                self.openai_proxy()
            elif not openai_proxy_url.startswith("http"):
                click.secho("输入的 OpenAI 代理地址不合法！仅可使用 http 代理", fg="bright_red", bold=True)
                self.openai_proxy()
            self.config["Bilibili"]["openai_proxy"] = openai_proxy_url

    def bilibili_username(self):
        username = InputPrompt("请输入 Bilibili 用户名: （可用于 AI 总结时获取 Bilibili 的 AI 字幕）").prompt()
        if not username or username == "":
            self.config["Bilibili"]["username"] = username
            click.secho("用户名为空，已关闭对应功能！", fg="bright_red", bold=True)
            return 
        elif not username.isdigit():
            click.secho("用户名不合法！", fg="bright_red", bold=True)
            return self.bilibili_username()
        self.config["Bilibili"]["username"] = username
        self.bilibili_password()

    def bilibili_password(self):
        password = InputPrompt("请输入 Bilibili 密码: ", is_password=True).prompt()
        if not password:
            click.secho("密码不能为空！", fg="bright_red", bold=True)
            self.bilibili_password()
        self.config["Bilibili"]["password"] = password

    def use_bilibili_login(self):
        if self.config["Bilibili"]["username"]:
            use_bilibili_login = ListPrompt(
                "是否使用已登录的 Bilibili 账号进行动态监听？（警告：不推荐使用该功能，暂不可用）",
                [Choice("否（关闭）"), Choice("是（开启）")],
                allow_filter=False,
                annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
            ).prompt()
            self.config["Bilibili"]["use_login"] = use_bilibili_login.name == "是（开启）"
        else:
            self.config["Bilibili"]["use_login"] = False

    def wordcloud(self):
        if is_full:
            wordcloud = ListPrompt(
                "是否为视频和专栏内容制作词云？",
                [Choice("是（开启）"), Choice("否（关闭）")],
                allow_filter=False,
                annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
            ).prompt()
            self.config["Bilibili"]["use_wordcloud"] = wordcloud.name == "是（开启）"
        else:
            self.config["Bilibili"]["use_wordcloud"] = False

    def bcut_asr(self):
        if (
            self.config["Bilibili"]["openai_summarization"]
            or self.config["Bilibili"]["use_wordcloud"]
        ):
            bcut_asr = ListPrompt(
                "是否使用 Bilibili ASR 进行视频内容语音识别？（用于 AI 总结和词云制作）",
                [Choice("是（开启）"), Choice("否（关闭）")],
                allow_filter=False,
                annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
            ).prompt()
            self.config["Bilibili"]["use_bcut_asr"] = bcut_asr.name == "是（开启）"
        else:
            self.config["Bilibili"]["use_bcut_asr"] = False

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

            if self.skip_verify or self.verify_friend(master):
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
            if not self.skip_verify and not self.verify_friend(admin):
                click.secho("该 QQ 号不是 Bot 的好友！", fg="bright_red", bold=True)
                continue

            self.config["admins"].append(int(admin))

    def log_level(self):
        self.config["log_level"] = (
            ListPrompt(
                "请选择日志等级",
                [
                    Choice("INFO"),
                    Choice("DEBUG"),
                    Choice("WARNING"),
                ],
                allow_filter=False,
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
