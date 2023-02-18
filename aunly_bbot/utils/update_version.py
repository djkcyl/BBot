import httpx
import contextlib

from pathlib import Path
from importlib import metadata
from packaging.version import parse


def get_local_version():
    TOML_PATH = Path(__file__).parent.parent.parent.joinpath("pyproject.toml")

    RAW_TOML = TOML_PATH.read_text(encoding="utf-8") if TOML_PATH.exists() else ""

    return (
        RAW_TOML.split("version = ")[1].split("\n")[0].strip('"')
        if RAW_TOML
        else metadata.version("aunly_bbot")
    )


async def get_remote_version():
    with contextlib.suppress(Exception):
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://pypi.org/pypi/aunly-bbot/json")
            resp = resp.json()
            # 按照时间排序，取最新的版本
            return sorted(resp["releases"].keys(), key=parse)


async def update_version():
    local_version = get_local_version()
    remote_version = await get_remote_version()

    if local_version and remote_version and parse(local_version) < parse(remote_version[-1]):
        return parse(local_version), parse(remote_version[-1])
