import re
import httpx
import asyncio

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Image, Plain, Voice, FlashImage, Source

from core.control import Interval
from library.b23_extract import b23_extract
from library.bilibili_request import get_b23_url
from library.draw_bili_image import binfo_image_create

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
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
    video_info = await video_info_get(video_number) if video_number else None
    if video_info:
        if video_info["code"] != 0:
            await Interval.manual(member.id)
            return await app.send_group_message(
                group, MessageChain([Plain("视频不存在或解析失败")])
            )
        else:
            await Interval.manual(int(video_info["data"]["aid"]))
        try:
            logger.info(f"开始生成视频信息图片：{video_info['data']['aid']}")
            b23_url = await get_b23_url(
                f"https://www.bilibili.com/video/{video_info['data']['bvid']}"
            )
            image = await asyncio.to_thread(binfo_image_create, video_info, b23_url)
            await app.send_group_message(
                group,
                MessageChain(
                    Image(data_bytes=image),
                    f"\n{b23_url}",
                ),
            )
        except Exception as err:
            logger.error(err)
            await app.send_group_message(
                group, MessageChain("视频解析 API 调用出错"), quote=source
            )


async def video_info_get(id):
    async with httpx.AsyncClient() as client:
        if id[:2] == "av":
            video_info = await client.get(
                f"http://api.bilibili.com/x/web-interface/view?aid={id[2:]}"
            )
            video_info = video_info.json()
        elif id[:2] == "BV":
            video_info = await client.get(
                f"http://api.bilibili.com/x/web-interface/view?bvid={id}"
            )
            video_info = video_info.json()
        else:
            raise ValueError("视频 ID 格式错误，只可为 av 或 BV")
        return video_info
