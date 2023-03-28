import sys
import httpx
import asyncio

from yarl import URL
from io import BytesIO
from pathlib import Path
from loguru import logger
from zipfile import ZipFile
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)

from ..core.bot_config import BotConfig


DEFUALT_DYNAMIC_FONT = "HarmonyOS_Sans_SC_Medium.ttf"


font_path = Path("data", "font")
font_mime_map = {
    "collection": "font/collection",
    "otf": "font/otf",
    "sfnt": "font/sfnt",
    "ttf": "font/ttf",
    "woff": "font/woff",
    "woff2": "font/woff2",
}
font_path.mkdir(parents=True, exist_ok=True)


async def get_font(font: str = DEFUALT_DYNAMIC_FONT):
    logger.debug(f"font: {font}")
    url = URL(font)
    if url.is_absolute():
        if font_path.joinpath(url.name).exists():
            logger.debug(f"Font {url.name} found in local")
            return font_path.joinpath(url.name)
        else:
            logger.warning(f"字体 {font} 不存在，尝试从网络获取")
            async with httpx.AsyncClient() as client:
                resp = await client.get(font)
                if resp.status_code != 200:
                    raise ConnectionError(f"字体 {font} 获取失败")
                font_path.joinpath(url.name).write_bytes(resp.content)
                return font_path.joinpath(url.name)
    else:
        if not font_path.joinpath(font).exists():
            raise FileNotFoundError(f"字体 {font} 不存在")
        logger.debug(f"Font {font} found in local")
        return font_path.joinpath(font)


def get_font_sync(font: str = DEFUALT_DYNAMIC_FONT):
    return asyncio.run(get_font(font))


def font_init():
    # sourcery skip: extract-method
    font_url = (
        "https://mirrors.bfsu.edu.cn/pypi/web/packages/ad/97/"
        "03cd0a15291c6c193260d97586c4adf37a7277d8ae4507d68566c5757a6a/"
        "bbot_fonts-0.1.1-py3-none-any.whl"
    )
    lock_file = Path("data", "font", ".lock")
    lock_file.touch(exist_ok=True)
    if lock_file.read_text() != font_url:
        font_file = BytesIO()
        with Progress(
            "{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeElapsedColumn(),
        ) as progress_bar:
            task = progress_bar.add_task("下载字体文件中", start=False)
            with httpx.stream("GET", font_url) as r:
                content_length = int(r.headers["Content-Length"])
                progress = 0
                progress_bar.update(task, total=content_length)
                progress_bar.update(task, completed=0)
                for chunk in r.iter_bytes():
                    font_file.write(chunk)
                    progress += len(chunk)
                    percent = progress / content_length * 100
                    progress_bar.advance(task, advance=percent)
                progress_bar.update(task, completed=content_length)
        with ZipFile(font_file) as z:
            fonts = [i for i in z.filelist if str(i.filename).startswith("bbot_fonts/font/")]
            for font in fonts:
                file_name = Path(font.filename).name
                local_file = font_path.joinpath(file_name)
                if not local_file.exists():
                    logger.info(local_file)
                    local_file.write_bytes(z.read(font))

        lock_file.write_text(font_url)
    else:
        logger.info("字体文件已存在，跳过下载")

    if BotConfig.Bilibili.dynamic_font:
        if BotConfig.Bilibili.dynamic_font_source == "remote":
            custom_font = URL(BotConfig.Bilibili.dynamic_font)
            if custom_font.is_absolute():
                if custom_font.name != URL(DEFUALT_DYNAMIC_FONT).name:
                    logger.info(get_font_sync(BotConfig.Bilibili.dynamic_font))
            else:
                logger.error("你输入的自定义字体不是一个有效的 URL，请检查！")
                sys.exit()
        else:
            custom_font = font_path.joinpath(BotConfig.Bilibili.dynamic_font)
            if not custom_font.exists():
                logger.error("你输入的自定义字体不存在（data/font），请检查！")
                sys.exit()
