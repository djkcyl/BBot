import re

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Image, Plain, Voice, FlashImage, Source

from library.b23_extract import b23_extract
from core.control import Interval, Permission
from library.draw_bili_image import binfo_image_create
from library.bilibili_request import get_b23_url, hc, grpc_get_view_info

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[Permission.require()]))
async def bilibili_main(
    app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source
):
    if message.has(Image) or message.has(Voice) or message.has(FlashImage):
        return

    message_str = message.as_persistent_string()
    if "b23.tv" in message_str:
        message_str = await b23_extract(message_str) or message_str
    p = re.compile(r"av(\d{1,15})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})")
    video_number = p.search(message_str)
    if video_number:
        video_number = video_number[0]
    else:
        return await Interval.manual(member.id)
    try:
        video_info = await video_info_get(video_number)
    except Exception:
        capture_exception()
        await Interval.manual(member.id)
        return await app.send_group_message(group, MessageChain([Plain("视频不存在或解析失败")]))
    await Interval.manual(video_info.arc.aid)
    try:
        logger.info(f"开始生成视频信息图片：{video_info.arc.aid}")
        b23_url = await get_b23_url(f"https://www.bilibili.com/video/{video_info.bvid}")
        image = await binfo_image_create(video_info, b23_url)
        await app.send_group_message(
            group,
            MessageChain(
                Image(data_bytes=image),
                f"\n{b23_url}",
            ),
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
        video_info = await grpc_get_view_info(aid=int(vid_id[2:]))
    elif vid_id[:2].upper() == "BV":
        video_info = await grpc_get_view_info(bvid=vid_id)
    else:
        raise ValueError("视频 ID 格式错误，只可为 av 或 BV")
    return video_info
