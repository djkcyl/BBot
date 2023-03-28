from loguru import logger

from ..model.exception import AbortError
from .bilibili_request import get_player, hc


async def get_subtitle_url(aid: int, cid: int) -> str:
    video_player = await get_player(aid, cid)
    subtitles_raw: list[dict] = video_player["subtitle"]["subtitles"]
    logger.debug(subtitles_raw)

    if not subtitles_raw:
        raise AbortError("未找到字幕")

    logger.debug(subtitles_raw)
    ai_subtitles = {}
    manual_subtitles = {}
    preferred_subs = ["zh-Hans", "en-US"]

    for subtitle in subtitles_raw:
        if "自动生成" in subtitle["lan_doc"]:
            ai_subtitles[subtitle["lan"]] = subtitle["subtitle_url"]
        else:
            manual_subtitles[subtitle["lan"]] = subtitle["subtitle_url"]

    if not manual_subtitles:
        return next(iter(ai_subtitles.values()))

    for sub in preferred_subs:
        if sub in manual_subtitles:
            return manual_subtitles[sub]

    return next(iter(manual_subtitles.values()))


async def get_subtitle(aid: int, cid: int) -> list[str]:
    subtitle_url = await get_subtitle_url(aid, cid)
    logger.debug(subtitle_url)
    subtitle = await hc.get(f"https:{subtitle_url}")
    if subtitle.status_code != 200:
        logger.warning(f"字幕获取失败：{aid} {cid}，状态码：{subtitle.status_code}，内容：{subtitle.text}")
        raise AbortError("字幕下载失败")
    logger.info(f"字幕获取成功：{aid} {cid}")
    return [x["content"] for x in subtitle.json()["body"]]
