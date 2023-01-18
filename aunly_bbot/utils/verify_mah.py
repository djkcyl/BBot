import httpx
import click

from yarl import URL
from json import JSONDecodeError


def verify_mirai(host: str, account: int, verify_key: str):
    try:
        if not URL(host).is_absolute():
            return click.secho("Mirai HTTP API 地址不合法", fg="bright_red", bold=True)
    except Exception:
        return click.secho("Mirai HTTP API 地址不合法", fg="bright_red", bold=True)

    if httpx.get(f"{host}/about").json()["data"]["version"] < "2.6.1":
        return click.secho(
            "Mirai HTTP API 版本低于 2.6.1，可能会导致部分功能无法使用！请升级至最新版", fg="bright_red", bold=True
        )

    try:
        verify = httpx.post(f"{host}/verify", json={"verifyKey": verify_key}).json()
        if verify["code"] != 0:
            return click.secho("Mirai HTTP API 的 verifyKey 错误！", fg="bright_red", bold=True)

        bind = httpx.post(
            f"{host}/bind", json={"sessionKey": verify["session"], "qq": account}
        ).json()
        if bind["code"] != 0:
            return click.secho(
                f"Mirai HTTP API 验证错误：{bind['msg']}！", fg="bright_red", bold=True
            )
    except httpx.HTTPError:
        return click.secho("无法连接到 Mirai HTTP API，请检查地址是否正确！", fg="bright_red", bold=True)
    except JSONDecodeError:
        return click.secho("输入的地址不为 Mirai HTTP API 的地址！", fg="bright_red", bold=True)

    if (
        httpx.post(
            f"{host}/release", json={"sessionKey": verify["session"], "qq": account}
        ).json()["code"]
        == 0
    ):
        return True
