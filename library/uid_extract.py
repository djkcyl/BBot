import re

from .b23_extract import b23_extract


async def uid_extract(text):
    b23_msg = await b23_extract(text) if "b23.tv" in text else None
    message = b23_msg or text
    pattern = re.compile("^[0-9]*$|bilibili.com/([0-9]*)")
    if match := pattern.search(message):
        return match[1] or match[0]
