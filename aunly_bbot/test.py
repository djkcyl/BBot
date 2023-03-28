import json
import httpx

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from .core.control import Permission

# from .utils.wordcloud import get_frequencies, get_wordcloud

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/test")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def main(app: Ariadne, group: Group):

    sub = httpx.get(
        "https://i0.hdslb.com/bfs/ai_subtitle/prod/31087008110492590207e0082656e40ce338d18289396914ffe"
    ).json()
    subs = [x["content"] for x in sub["body"]]
    title = ""
    description = ""

    word_counts = get_frequencies(subs)
    word_cloud = await get_wordcloud(word_counts)

    # browser_context = app.launch_manager.get_interface(PlaywrightContext).context
    # page = await browser_context.new_page()
    # await page.set_viewport_size({"width": 460, "height": 100})
    # if req.error:
    #     print(req.message)
    #     return
    # md = convert_md(req.summary)
    # css = "\n".join(BuiltinCSS.github.value)
    # await page.set_content(
    #     '<html><head><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    #     f"<style>{css}</style></head><body>{md}<body></html>"
    # )
    # result = await page.screenshot(full_page=True, type="jpeg", quality=95)

    await app.send_group_message(group, MessageChain(Image(data_bytes=word_cloud)))
