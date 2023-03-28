import re

from loguru import logger
from graia.ariadne.app import Ariadne

from .openai import openai_req, get_small_size_transcripts, get_user_prompt, get_simple_prompt


async def subtitle_summarise(sub: list[str], title: str):
    small_size_transcripts = get_small_size_transcripts(sub)
    prompt = get_user_prompt(title, small_size_transcripts)
    logger.debug(prompt)
    return await openai_req(get_simple_prompt(prompt))


async def column_summarise(cv_title: str, cv_text: str):
    sentences = re.split(r"[，。；,.;\n]+", cv_text)
    small_size_transcripts = get_small_size_transcripts(sentences)
    prompt = get_user_prompt(cv_title, small_size_transcripts)
    logger.debug(prompt)
    return await openai_req(get_simple_prompt(prompt))


async def get_browser_image(data: str):
    from graiax.text2img.playwright import convert_md
    from graiax.playwright.interface import PlaywrightContext
    from graiax.text2img.playwright.renderer import BuiltinCSS

    app = Ariadne.current()
    browser_context = app.launch_manager.get_interface(PlaywrightContext).context
    page = await browser_context.new_page()
    await page.set_viewport_size({"width": 400, "height": 100})
    md = convert_md(data)
    css = "\n".join(BuiltinCSS.github.value)
    await page.set_content(
        '<html><head><meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f"<style>{css}</style></head><body>{md}<body></html>"
    )
    return await page.screenshot(full_page=True, type="jpeg", quality=95)
