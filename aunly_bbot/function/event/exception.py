import traceback

from io import StringIO
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from sentry_sdk import capture_exception
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya.builtins.broadcast.schema import ListenerSchema

from ...core.bot_config import BotConfig
from ...utils.text2image import text2image


channel = Channel.current()


async def make_msg_for_unknown_exception(event: ExceptionThrowed):
    capture_exception(event.exception)
    with StringIO() as fp:
        traceback.print_tb(event.exception.__traceback__, file=fp)
        tb = fp.getvalue()
    msg = str(
        f"异常事件：\n{str(event.event)}"
        + f"\n \n异常类型：\n{type(event.exception)}"
        + f"\n \n异常内容：\n{str(event.exception)}"
        + f"\n \n异常追踪：\n{tb}\n{str(event.exception)}"
    )
    image = await text2image(msg, 200)
    return MessageChain("发生未捕获的异常\n", Image(data_bytes=image))


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def main(event: ExceptionThrowed):
    if isinstance(event.event, ExceptionThrowed):
        return
    app = Ariadne.current()
    eimg = await make_msg_for_unknown_exception(event)
    return await app.send_friend_message(
        BotConfig.master,
        eimg,
    )
