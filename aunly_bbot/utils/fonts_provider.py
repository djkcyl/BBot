import sys
import httpx
import asyncio

from yarl import URL
from io import BytesIO
from pathlib import Path
from loguru import logger
from zipfile import ZipFile

from ..core.bot_config import BotConfig


DEFUALT_DYNAMIC_FONT = (
    "https://cdn.jsdelivr.net/gh/" "djkcyl/BBot-Fonts/HarmonyOS_Sans_SC_Medium.woff2"
)


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
    f = httpx.get(
        "https://mirrors.bfsu.edu.cn/pypi/web/packages/ad/97/"
        "03cd0a15291c6c193260d97586c4adf37a7277d8ae4507d68566c5757a6a/"
        "bbot_fonts-0.1.1-py3-none-any.whl"
    )
    with ZipFile(BytesIO(f.content)) as z:
        font_path = Path("data", "font")
        font_path.mkdir(parents=True, exist_ok=True)
        fonts = [i for i in z.filelist if str(i.filename).startswith("bbot_fonts/font/")]
        for font in fonts:
            file_name = Path(font.filename).name
            local_file = font_path.joinpath(file_name)
            if not local_file.exists():
                logger.info(local_file)
                local_file.write_bytes(z.read(font))
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
