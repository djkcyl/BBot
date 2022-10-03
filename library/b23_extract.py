import re

from loguru import logger

from library.bilibili_request import hc


async def b23_extract(text: str):
    if "b23.tv" not in text:
        return None
    if not (b23 := re.compile(r"b23.tv[\\/]+(\w+)").search(text)):
        return None
    try:
        url = f"https://b23.tv/{b23[1]}"
        resp = await hc.get(url, follow_redirects=True)
        url = resp.url
        logger.debug(f"b23.tv url: {url}")
        return str(url)
    except TypeError:
        return None
