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

from ..core.announcement import BBOT_ASCII_LOGO

data = {}


def is_qq(qq: str) -> bool:
    """判断是否为合法的 QQ 号"""
    return len(qq) >= 5 and len(qq) <= 17 if qq.isdigit() else False


def verify_friend(qq: str) -> bool:
    """验证是否为好友"""
    friend_list = httpx.get(
        f"{data['mirai_host']}/friendList", params={"sessionKey": data["session"]}
    ).json()["data"]
    return any(friend["id"] == int(qq) for friend in friend_list)


def mirai_account():
    mirai_account = InputPrompt("请输入你已经登录 Mirai 的 QQ 账号: ").prompt()
    if is_qq(mirai_account):
        data["qq"] = mirai_account
        return mirai_account
    click.secho("输入的 QQ 号不合法！", fg="red", bold=True)


def mirai_mirai_host():
    mirai_host = InputPrompt("请输入 Mirai HTTP API 的地址: ", "http://localhost:8080").prompt()
    if URL(mirai_host).is_absolute():
        try:
            if httpx.get(f"{mirai_host}/about").json()["data"]["version"] >= "2.6.1":
                data["mirai_host"] = mirai_host
                return mirai_host
            click.secho("Mirai HTTP API 版本低于 2.6.1，可能会导致部分功能无法使用！请升级至最新版", fg="red", bold=True)
        except httpx.HTTPError:
            click.secho("无法连接到 Mirai HTTP API，请检查地址是否正确！", fg="red", bold=True)
    else:
        click.secho("输入的地址不合法！", fg="red", bold=True)


def mirai_verify_key():
    mirai_key: str = InputPrompt("请输入 Mirai HTTP API 的 verifyKey: ", is_password=True).prompt()
    try:
        verify = httpx.post(
            f"{data['mirai_host']}/verify", json={"verifyKey": mirai_key}
        ).json()
        if verify["code"] == 0:
            data["mirai_key"] = mirai_key
            data["session"] = verify["session"]
            bind = httpx.post(
                f"{data['mirai_host']}/bind",
                json={"sessionKey": data["session"], "qq": data["qq"]},
            ).json()
            if bind["code"] == 0 and (
                httpx.get(
                    f"{data['mirai_host']}/sessionInfo",
                    params={"sessionKey": data["session"]},
                ).json()["code"]
                == 0
            ):
                click.secho("Mirai HTTP API 验证成功！", fg="green", bold=True)
                return mirai_key
            else:
                click.secho(f"Mirai HTTP API 验证错误，{bind['msg']}！", fg="red", bold=True)
                raise CancelledError
        else:
            click.secho("Mirai HTTP API 的 verifyKey 错误！", fg="red", bold=True)

    except httpx.HTTPError:
        click.secho("无法连接到 Mirai HTTP API，请检查地址是否正确！", fg="red", bold=True)
    except JSONDecodeError:
        click.secho("输入的地址不为 Mirai HTTP API 的地址！", fg="red", bold=True)


def master():
    master = InputPrompt("请输入你的 QQ 号: ").prompt()
    if not master.isdigit():
        click.secho("输入的 QQ 号不合法！", fg="red", bold=True)
        return
    data["master"] = int(master)

    if verify_friend(master):
        return int(master)
    else:
        click.secho("你输入的 QQ 号不是 Bot 的好友！", fg="red", bold=True)


def debug():
    debug = ListPrompt(
        "是否开启调试模式？（开启后 Bot 将只会相应调试群的消息）",
        [Choice("是（开启）"), Choice("否（关闭）")],
        allow_filter=False,
        default_select=1,
        annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
    ).prompt()
    if debug.name == "是（开启）":
        data["debug"] = True
        return True
    else:
        data["debug"] = False
        return False


def debug_group():
    if not data["debug"]:
        return [123456789]
    debug_group_list: list[int] = []
    while True:
        debug_group = InputPrompt("请输入调试群的群号: ").prompt()
        if not debug_group.isdigit():
            click.secho("输入的群号不合法！", fg="red", bold=True)
            continue
        if int(debug_group) in debug_group_list:
            click.secho("该群已在调试群列表中，请重新输入！", fg="red", bold=True)
            continue
        debug_group = int(debug_group)
        data["debug_group"] = debug_group
        group_list = httpx.get(
            f"{data['mirai_host']}/groupList", params={"sessionKey": data["session"]}
        ).json()["data"]

        for group in group_list:
            if group["id"] == debug_group:
                debug_group_list.append(debug_group)
                break
        else:
            click.secho("Bot 未加入该群，请重新输入！", fg="red", bold=True)

        if not ConfirmPrompt("是否继续添加？", default_choice=False).prompt():
            break

    return debug_group_list


def bilibili_mobile_style():
    mobile_style = ListPrompt(
        "是否使用手机端样式？",
        [Choice("是（开启）"), Choice("否（关闭）")],
        allow_filter=False,
        annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
    ).prompt()
    if mobile_style.name == "是（开启）":
        data["mobile_style"] = True
        return True
    else:
        data["mobile_style"] = False
        return False


def bilibili_concurrent():
    concurrent = InputPrompt("请输入并发数（理论该值越大推送效率越高）: ", default_text="10").prompt()
    if concurrent.isdigit() and 50 >= int(concurrent) > 0:
        data["concurrent"] = int(concurrent)
        return concurrent
    click.secho("输入的并发数不合法！请输入 1 - 50 之间的整数", fg="red", bold=True)
    return


def event():
    event_map = {"禁言": "mute", "权限变更": "permission", "动态推送": "push", "UP 订阅": "subscribe"}
    event_list = CheckboxPrompt(
        "请选择需要私聊管理员推送的事件",
        [Choice("禁言"), Choice("权限变更"), Choice("动态推送"), Choice("UP 订阅")],
        default_select=[0, 1, 2, 3],
        annotation="使用键盘的 ↑ 和 ↓ 来选择, 按空格开关, 按回车确认",
    ).prompt()
    return {event_map[event.name]: True for event in event_list}


def webui():
    webui = ListPrompt(
        "是否开启 WebUI？",
        [Choice("是（开启）"), Choice("否（关闭）")],
        allow_filter=False,
        annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
    ).prompt()
    data["webui"] = webui.name == "是（开启）"
    return data["webui"]


def webui_data():
    if not data["webui"]:
        return {"webui_host": "0.0.0.0", "webui_port": 6080}
    webui_url = InputPrompt("请输入 WebUI 的地址: ", default_text="http://0.0.0.0:6080").prompt()
    webui_url = URL(webui_url)
    if webui_url.is_absolute():
        return {"webui_host": webui_url.host, "webui_port": webui_url.port}
    click.secho("输入的地址不合法！", fg="red", bold=True)


def log_level():
    level = ListPrompt(
        "请选择日志等级",
        [Choice("DEBUG"), Choice("INFO"), Choice("WARNING")],
        allow_filter=False,
        default_select=1,
        annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
    ).prompt()
    return level.name


def name():
    bot_name = InputPrompt("请输入 Bot 的昵称: ", default_text="BBot").prompt()
    if 0 < len(bot_name) <= 16:
        data["bot_name"] = bot_name
        return bot_name
    click.secho("输入的昵称不合法（请输入 1 - 16 位字符）", fg="red", bold=True)


def admins():
    admin_list = []
    while True:
        admin = InputPrompt("请输入管理员的 QQ 号: ", default_text=str(data["master"])).prompt()
        if admin.isdigit() and is_qq(admin):
            if int(admin) in admin_list:
                click.secho("该 QQ 号已经在管理员列表中了！", fg="red", bold=True)
                continue
            if verify_friend(admin):
                admin_list.append(int(admin))
                if ConfirmPrompt("是否继续添加？", default_choice=False).prompt():
                    continue
                return admin_list
            else:
                click.secho("该 QQ 号不是你的好友！", fg="red", bold=True)
        click.secho("输入的 QQ 号不合法！", fg="red", bold=True)


def max_subscriptions():
    max_subscriptions = InputPrompt("请输入每个群的最大订阅数: ", default_text="4").prompt()
    if max_subscriptions.isdigit() and 0 < int(max_subscriptions) <= 100:
        data["max_subscriptions"] = int(max_subscriptions)
        return int(max_subscriptions)
    click.secho("输入的订阅数不合法！请输入 1 - 100 之间的整数", fg="red", bold=True)


def access_control():
    access_control = ListPrompt(
        "是否开启白名单控制？（仅允许加入白名单中的群）",
        [Choice("是（开启）"), Choice("否（关闭）")],
        allow_filter=False,
        annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
    ).prompt()
    data["access_control"] = access_control.name == "是（开启）"
    return data["access_control"]


config_list = [
    mirai_account,
    mirai_mirai_host,
    mirai_verify_key,
    master,
    debug,
    debug_group,
    bilibili_mobile_style,
    bilibili_concurrent,
    event,
    webui,
    webui_data,
    log_level,
    name,
    admins,
    max_subscriptions,
    access_control,
]


def click_config():
    click.secho(BBOT_ASCII_LOGO, fg="bright_blue", bold=True)
    click.secho("\n欢迎使用 BBot 配置向导！\n", fg="green", bold=True)
    # click.secho("配置向导仍在开发，暂不可用。", fg="red", bold=True)
    # return
    click.secho("请按照提示输入相关信息。\n", fg="yellow")

    try:
        if list(Path(".").iterdir()):
            click.secho("当前目录不为空，可能会导致未知的错误。", fg="yellow", bold=True)
            click.secho("请确保当前目录没有 Bot 之外的文件。", fg="yellow", bold=True)

            if not ConfirmPrompt("是否仍要继续配置流程？", default_choice=False).prompt():
                return

        config_method = ListPrompt(
            "请选择你要使用的配置方式：",
            [
                Choice("使用 Web 配置向导", "web"),
                Choice("使用命令行配置向导", "cli"),
                Choice("手动修改配置文件", "file"),
            ],
            annotation="使用键盘的 ↑ 和 ↓ 来选择, 按回车确认",
        ).prompt()

        if config_method.data == "web":
            click.secho("Web 配置向导暂不可用。", fg="red", bold=True)
        elif config_method.data == "cli":
            BotConfig.save_cli(cli_config())
        else:
            BotConfig.create()
            click.secho("配置文件已创建（data/bot_config.yaml）。请手动打开后进行编辑。", fg="green", bold=True)
            while True:
                if ConfirmPrompt("是否完成了配置？", default_choice=False).prompt():
                    config_verify = BotConfig.verify()
                    if not config_verify:
                        break
                    click.secho("配置文件有误，请检查后重试。错误信息如下：", fg="red", bold=True)
                    click.secho(config_verify, fg="red", bold=True)

        click.secho("恭喜你，配置已完成！\n", fg="green", bold=True)
        click.secho("现在，你可以使用 bbot run 命令运行 BBot 了。", fg="blue", bold=True)

    except CancelledError:
        click.secho("配置向导已取消。", fg="yellow", bold=True)


def cli_config():
    global data

    config_data = {}

    for config_prompt in config_list:
        while True:
            result = config_prompt()
            if result is None:
                continue
            config_data[config_prompt.__name__] = result
            break

    if data.get("session", None):
        httpx.post(
            f"{data['mirai_host']}/release",
            json={"sessionKey": data["session"], "qq": data["qq"]},
        )
    data = {}

    return config_data
