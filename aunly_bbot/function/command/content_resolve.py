import json
import asyncio

from loguru import logger
from graia.saya import Channel
from grpc.aio import AioRpcError
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from bilireq.exceptions import GrpcError
from graia.ariadne.model import Group, Member
from httpx._exceptions import TimeoutException
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema

from ...core.bot_config import BotConfig
from ...model.exception import AbortError
from ...utils.column_resolve import get_cv
from ...core.data import ContentResolveData
from ...core.control import Interval, Permission
from ...utils.video_subtitle import get_subtitle
from ...utils.bilibili_parse import extract_bilibili_info
from ...utils.draw_bili_image import binfo_image_create
from ...utils.text2image import rich_text2image, browser_text2image
from ...utils.bilibili_request import get_b23_url, grpc_get_view_info
from ...utils.content_summarise import column_summarise, subtitle_summarise

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[Permission.require()]))
async def main(
    app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source
):
    bili_number = await extract_bilibili_info(message)
    if not bili_number:
        return

    if bili_number[:2] in ["BV", "bv", "av"]:
        try:
            if (video_info := await video_info_get(bili_number)) is None:
                await Interval.manual(group.id, 5)
                return
            elif video_info.ecode == 1:
                await app.send_group_message(
                    group, MessageChain(f"未找到视频 {bili_number}，可能已被 UP 主删除。"), quote=source
                )
                return
        except (AioRpcError, GrpcError) as e:
            await Interval.manual(group.id, 5)
            logger.exception(e)
            return await app.send_group_message(
                group, MessageChain(f"{bili_number} 视频信息获取失败，错误信息：{type(e)} {e}"), quote=source
            )
        except Exception as e:
            capture_exception()
            await Interval.manual(group.id, 5)
            logger.exception(e)
            return await app.send_group_message(
                group, MessageChain(f"{bili_number} 视频信息解析失败，错误信息：{type(e)} {e}"), quote=source
            )
        aid = video_info.activity_season.arc.aid or video_info.arc.aid
        cid = (
            video_info.activity_season.pages[0].page.cid
            if video_info.activity_season.pages
            else video_info.pages[0].page.cid
        )
        bvid = video_info.activity_season.bvid or video_info.bvid
        title = video_info.activity_season.arc.title or video_info.arc.title
        archive_data = ContentResolveData(aid=aid)
        archive_data.title = title
        await Interval.manual(aid + group.id, 30)
        try:
            logger.info(f"开始生成视频信息图片：{aid}")
            b23_url = await get_b23_url(f"https://www.bilibili.com/video/{bvid}")
            image = await binfo_image_create(video_info, b23_url)
            info_message = await app.send_group_message(
                group,
                MessageChain(
                    Image(data_bytes=image),
                    f"\n{b23_url}",
                ),
                quote=source,
            )

            if BotConfig.Bilibili.openai_summarization or BotConfig.Bilibili.use_wordcloud:
                try:
                    if archive_data.content:
                        subtitle = [str(x) for x in json.loads(archive_data.content)]
                    else:
                        subtitle = await get_subtitle(aid, cid)
                        archive_data.content = json.dumps(subtitle, ensure_ascii=False)

                    if (
                        len(subtitle) < 10
                        or video_info.arc.duration < BotConfig.Bilibili.asr_length_threshold
                    ):
                        raise AbortError("字幕内容过少且视频时长过短，跳过总结请求")

                    chatgpt_thinks = True

                    async def openai_summarization():
                        logger.info(f"开始进行 AI 总结：{aid}")
                        try:
                            if archive_data.openai:
                                logger.info(f"{aid} 已存在总结缓存，跳过总结请求")
                                summarise = archive_data.openai
                            else:
                                logger.info(f"{aid} 总结不存在，正在尝试请求......")
                                try:
                                    await Interval.manual(member, 600)
                                except ExecutionStop:
                                    msg = f"{member.id} 在 10 分钟内已经请求过总结，跳过本次请求"
                                    logger.info(msg)
                                    raise AbortError(msg)
                                ai_summary = await subtitle_summarise(subtitle, title)
                                if ai_summary.summary:
                                    summarise = ai_summary.summary
                                    archive_data.openai = summarise
                                else:
                                    logger.warning(f"视频 {aid} 总结失败：{ai_summary.raw}")
                                    return

                            if "no meaning" in summarise.lower() or len(summarise) < 20:
                                nonlocal chatgpt_thinks
                                chatgpt_thinks = False
                                raise AbortError("ChatGPT 认为这些字幕没有意义")

                            logger.debug(summarise)
                            if BotConfig.Bilibili.use_browser:
                                image = await browser_text2image(summarise)
                            else:
                                image = await rich_text2image(summarise)
                            if image:
                                images.append(image)
                        except AbortError as e:
                            logger.warning(f"视频 {aid} 总结被终止：{e}")
                        except Exception:
                            capture_exception()
                            logger.exception(f"视频 {aid} 总结出错")

                    async def wordcloud():
                        logger.info(f"开始生成词云：{aid}")
                        try:
                            from ...utils.wordcloud import get_worldcloud_image, get_frequencies

                            if archive_data.jieba:
                                logger.info(f"{aid} 已存在分词缓存，跳过分词")
                                word_frequencies = dict(json.loads(archive_data.jieba))
                            else:
                                logger.info(f"{aid} 分词不存在，正在尝试分词......")
                                word_frequencies = await asyncio.to_thread(
                                    get_frequencies, subtitle
                                )
                                archive_data.jieba = json.dumps(
                                    word_frequencies, ensure_ascii=False
                                )

                            wordcloud = await get_worldcloud_image(word_frequencies)
                            if wordcloud:
                                images.append(wordcloud)
                        except Exception:
                            capture_exception()
                            logger.exception(f"视频 {aid} 词云出错")

                    images = []
                    if BotConfig.Bilibili.openai_summarization:
                        await openai_summarization()
                    if BotConfig.Bilibili.use_wordcloud and chatgpt_thinks:
                        await wordcloud()

                    if images:
                        await app.send_group_message(
                            group,
                            MessageChain([Image(data_bytes=x) for x in images]),
                            quote=info_message.source,
                        )

                except AbortError as e:
                    logger.warning(f"视频 {aid} 总结失败：{e.message}")
                    return
                archive_data.save()

        except TimeoutException:
            await app.send_group_message(
                group, MessageChain(f"{bili_number} 视频信息生成超时，请稍后再试。"), quote=source
            )
        except Exception as e:
            capture_exception()
            logger.exception("视频解析 API 调用出错")
            await app.send_group_message(
                group, MessageChain(f"视频解析 API 调用出错：{e}"), quote=source
            )

    elif bili_number[:2] == "cv":
        if BotConfig.Bilibili.openai_summarization or BotConfig.Bilibili.use_wordcloud:
            column_id = bili_number[2:]
            archive_data = ContentResolveData(cid=column_id)
            try:
                if archive_data.content and archive_data.title:
                    cv_text = archive_data.content
                    cv_title = archive_data.title
                else:
                    cv_title, cv_text = await get_cv(column_id)
                    archive_data.title = cv_title
                    archive_data.content = cv_text

                async def openai_summarization():
                    try:
                        if archive_data.openai:
                            summarise = archive_data.openai
                        else:
                            ai_summary = await column_summarise(cv_title, cv_text)
                            if ai_summary.summary:
                                summarise = ai_summary.summary
                                archive_data.openai = summarise
                            else:
                                return

                        if BotConfig.Bilibili.use_browser:
                            image = await browser_text2image(summarise)
                        else:
                            image = await rich_text2image(summarise)
                        if image:
                            await app.send_group_message(
                                group, MessageChain(Image(data_bytes=image)), quote=source
                            )
                    except AbortError as e:
                        logger.warning(f"专栏 {column_id} 总结被终止：{e}")
                    except Exception:
                        capture_exception()
                        logger.exception(f"专栏 {column_id} 总结出错")

                async def wordcloud():
                    try:
                        from ...utils.wordcloud import get_worldcloud_image, get_frequencies

                        if archive_data.jieba:
                            word_frequencies = dict(json.loads(archive_data.jieba))
                        else:
                            word_frequencies = await asyncio.to_thread(
                                get_frequencies, [cv_title, cv_text]
                            )
                            archive_data.jieba = json.dumps(
                                word_frequencies, ensure_ascii=False
                            )

                        wordcloud = await get_worldcloud_image(word_frequencies)
                        if wordcloud:
                            await app.send_group_message(
                                group, MessageChain(Image(data_bytes=wordcloud)), quote=source
                            )
                    except Exception:
                        capture_exception()
                        logger.exception(f"专栏 {column_id} 词云出错")

                gather = []
                if BotConfig.Bilibili.openai_summarization:
                    gather.append(openai_summarization())
                if BotConfig.Bilibili.use_wordcloud:
                    gather.append(wordcloud())
                await asyncio.gather(*gather, return_exceptions=True)
            except AbortError as e:
                logger.warning(f"专栏 {column_id} 加载失败：{e.message}")
            archive_data.save()


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
