import re

from loguru import logger
from graia.saya import Channel
from grpc.aio import AioRpcError
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from sentry_sdk import capture_exception
from bilireq.exceptions import GrpcError
from httpx._exceptions import TimeoutException
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Image, Voice, FlashImage, Source

from ...utils.b23_extract import b23_extract
from ...core.control import Interval, Permission
from ...utils.draw_bili_image import binfo_image_create
from ...utils.bilibili_request import get_b23_url, grpc_get_view_info

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[Permission.require()]))
async def main(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if message.has(Image) or message.has(Voice) or message.has(FlashImage):
        return

    message_str = message.as_persistent_string(binary=False)
    p = re.compile(r"av(\d{1,15})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})")
    if not p.search(message_str) and ("b23.tv" in message_str or "b23.wtf" in message_str):
        message_str = await b23_extract(message_str) or message_str
    video_number = p.search(message_str)
    if video_number:
        video_number = video_number[0]
    else:
        return
    try:
        if (video_info := await video_info_get(video_number)) is None:
            await Interval.manual(group.id, 5)
            return
        elif video_info.ecode == 1:
            await app.send_group_message(
                group, MessageChain(f"未找到视频 {video_number}，可能已被 UP 主删除。"), quote=source
            )
            return
    except (AioRpcError, GrpcError) as e:
        await Interval.manual(group.id, 5)
        logger.exception(e)
        return await app.send_group_message(
            group, MessageChain(f"{video_number} 视频信息获取失败，错误信息：{type(e)} {e}"), quote=source
        )
    except Exception as e:
        capture_exception()
        await Interval.manual(group.id, 5)
        logger.exception(e)
        return await app.send_group_message(
            group, MessageChain(f"{video_number} 视频信息解析失败，错误信息：{type(e)} {e}"), quote=source
        )
    aid = video_info.activity_season.arc.aid or video_info.arc.aid
    bvid = video_info.activity_season.bvid or video_info.bvid
    await Interval.manual(aid + group.id)
    try:
        logger.info(f"开始生成视频信息图片：{aid}")
        b23_url = await get_b23_url(f"https://www.bilibili.com/video/{bvid}")
        image = await binfo_image_create(video_info, b23_url)
        await app.send_group_message(
            group,
            MessageChain(
                Image(data_bytes=image),
                f"\n{b23_url}",
            ),
            quote=source,
        )
    except TimeoutException:
        await app.send_group_message(
            group, MessageChain(f"{video_number} 视频信息生成超时，请稍后再试。"), quote=source
        )
    except Exception as e:  # noqa
        capture_exception()
        logger.exception("视频解析 API 调用出错")
        await app.send_group_message(group, MessageChain(f"视频解析 API 调用出错：{e}"), quote=source)


def bv2av(bv):
    table = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
    tr = {table[i]: i for i in range(58)}
    s = [11, 10, 3, 8, 4, 6]
    xor = 177451812
    add = 8728348608
    r = sum(tr[bv[s[i]]] * 58**i for i in range(6))
    return (r - add) ^ xor


async def video_info_get(vid_id: str):
    if vid_id[:2].lower() == "av":
        aid = int(vid_id[2:])
        return await grpc_get_view_info(aid=aid) if aid > 1 else None
    return await grpc_get_view_info(bvid=vid_id)
