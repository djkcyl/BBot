import json
import time
import httpx

from pathlib import Path
from loguru import logger

from core.bot_config import BotConfig

from .mobile_login_bilibili import bilibiliMobile


head = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 6.1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/41.0.2228.0 "
        "Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}

login_cache_file = Path("data/login_cache.json")
bilibili_client = bilibiliMobile(BotConfig.Bilibili.username, BotConfig.Bilibili.password)
bilibili_token = None
token_json = None


def get_token():
    return bilibili_token


def set_token(token):
    global bilibili_token, token_json
    bilibili_token = token["data"]["token_info"]["access_token"]
    token_json = token


async def bilibili_login():
    if login_cache_file.exists():
        token_json = json.loads(login_cache_file.read_text())
        logger.info("[BiliBili推送] 已读取缓存的登录信息")
        set_token(token_json)
        return True, token_json
    else:
        resp = await bilibili_client.login()
        set_token(resp)
        save_token()
        return False, resp


def save_token():
    login_cache_file.write_text(json.dumps(token_json, indent=2))


async def get_status_info_by_uids(uids):
    for retry in range(3):
        try:
            async with httpx.AsyncClient(headers=head) as client:
                r = await client.post(
                    "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids",
                    json=uids,
                )
                return r.json()
        except httpx.HTTPError as e:
            logger.error(f"[BiliBili推送] API 访问失败，正在第 {retry + 1} 重试 {e}")
    logger.error("[BiliBili推送] API 访问连续失败，请检查")


async def relation_modify(uid, act: int):
    for retry in range(3):
        try:
            data = {
                "access_key": get_token(),
                "act": act,
                "appkey": "783bbb7264451d82",
                "build": "6700300",
                "channel": "yingyongbao",
                "c_locale": "zh_CN",
                "s_locale": "zh_CN",
                "disable_rcmd": "0",
                "extend_content": json.dumps({"entity": "user", "entity_id": str(uid)}),
                "mobi_app": "android",
                "platform": "android",
                "re_src": 31,
                "spmid": "main.space.0.0",
                "statistics": '{"appId":1,"platform":3,"version":"6.70.0","abtest":""}',
                "fid": uid,
                "ts": str(int(time.time())),
            }
            keys = sorted(data.keys())
            data_sorted = {key: data[key] for key in keys}
            data = data_sorted
            sign = bilibili_client.calcSign(data)
            data["sign"] = sign
            response = await bilibili_client.session.post(
                "https://api.bilibili.com/x/relation/modify",
                data=data,
                headers=bilibili_client.headers,
            )
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"[BiliBili推送] API 访问失败，正在第 {retry + 1} 重试 {e}")
