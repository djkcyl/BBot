import re
import httpx

from loguru import logger
from typing import Union, Optional

from data import get_sub_by_group

from .b23_extract import b23_extract


async def uid_extract(text: str, groupid: Optional[Union[int, str]] = None):
    logger.debug(f"[UID Extract] Original Text: {text}")
    if up_list := get_sub_by_group(groupid or 0):
        logger.debug(f"[UID Extract] Group {groupid} has {len(up_list)} Subscribers")
        if text.isdigit():
            logger.debug("[UID Extract] Text is a Number")
        for data in up_list:
            if text.isdigit():
                if data.uid == text:
                    logger.debug(
                        f"[UID Extract] Found UID from Group Subscribers: {data.uname}({data.uid})"
                    )
                    return str(data.uid)
            else:
                text_g = text.strip(""""'“”‘’""")
                if data.nick == text_g or data.uname == text_g:
                    logger.debug(
                        f"[UID Extract] Found UName from Group Subscribers: {data.uname}({data.uid})"
                    )
                    return str(data.uid)
        logger.debug("[UID Extract] No Subscriber found")
    b23_msg = await b23_extract(text) if "b23.tv" in text else None
    message = b23_msg or text
    logger.debug(f"[UID Extract] b23 extract: {message}")
    pattern = re.compile("^[0-9]*$|bilibili.com/([0-9]*)")
    if match := pattern.search(message):
        logger.debug(f"[UID Extract] Digit or Url: {match}")
        match = match[1] or match[0]
        return str(match)
    elif message.startswith("UID:"):
        pattern = re.compile("^\\d+")
        if match := pattern.search(message[4:]):
            logger.debug(f"[UID Extract] UID: {match}")
            return str(match[0])
    else:
        text_u = text.strip(""""'“”‘’""")
        if text_u != text:
            logger.debug(f"[UID Extract] Text is a Quoted Digit: {text_u}")
        logger.debug(f"[UID Extract] Searching UID in BiLiBili: {text_u}")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.bilibili.com/x/web-interface/search/type",
                params={"keyword": text_u, "search_type": "bili_user"},
            )
        resp = resp.json()
        logger.debug(f"[UID Extract] Search result: {resp}")
        data = resp["data"]
        if data["numResults"]:
            for result in data["result"]:
                if result["uname"] == text_u:
                    logger.debug(f"[UID Extract] Found User: {result}")
                    return str(result["mid"])
        logger.debug("[UID Extract] No User found")
