import sys
import httpx
import random
import asyncio
import tiktoken_async

from loguru import logger
from httpx import Response
from typing import Optional
from collections import OrderedDict

from ..core.bot_config import BotConfig
from ..model.openai import OpenAI, TokenUsage

LIMIT_COUNT = {
    "gpt-3.5-turbo-0613": 3500,
    "gpt-3.5-turbo-16k-0613": 15000,
    "gpt-4-0613": 7600,
}.get(BotConfig.Bilibili.openai_model or "gpt-3.5-turbo-0613", 3500)

if BotConfig.Bilibili.openai_summarization:
    logger.info("正在加载 OpenAI Token 计算模型")
    try:
        tiktoken_enc = asyncio.run(tiktoken_async.encoding_for_model(BotConfig.Bilibili.openai_model))
    except Exception as e:
        logger.warning(f"加载 OpenAI Token 计算模型失败，请重新启动，{e}")
        sys.exit(1)
    logger.info(f"{tiktoken_enc.name} 加载成功")


def get_summarise_prompt(title: str, transcript: str) -> list[dict[str, str]]:
    title = title.replace("\n", " ").strip() if title else ""
    transcript = transcript.replace("\n", " ").strip() if transcript else ""
    if BotConfig.Bilibili.openai_promot_version == 1:
        language = "Chinese"
        sys_prompt = (
            "Your output should use the following template:\n## Summary\n## Highlights\n"
            "- [Emoji] Bulletpoint\n\n"
            "Your task is to summarise the video I have given you in up to 2 to 6 concise bullet points. "
            "First, use a simple sentence to summarize, each bullet point is at least 15 words. "
            "Choose an appropriate emoji for each bullet point. "
            "Use the video above: {{Title}} {{Transcript}}."
            "\nIf you think that the content in the transcript is meaningless, "
            "Or if there is very little content that cannot be well summarized, "
            "then you can simply output the two words 'no meaning'. Remember, not to output anything else."
        )
        return get_full_prompt(f'Title: "{title}"\nTranscript: "{transcript}"', sys_prompt, language)
    return get_full_prompt(
        prompt=(
            "使用以下Markdown模板为我总结视频字幕数据，除非字幕中的内容无意义，或者内容较少无法总结，或者未提供字幕数据，或者无有效内容，你就不使用模板回复，只回复“无意义”："
            "\n## 概述"
            "\n{内容，尽可能精简总结内容不要太详细}"
            "\n## 要点"
            "\n- {使用不重复并合适的emoji，仅限一个，禁止重复} {内容不换行大于15字，可多项，条数与有效内容数量呈正比}"
            "\n不要随意翻译任何内容。仅使用中文总结。"
            "\n不说与总结无关的其他内容，你的回复仅限固定格式提供的“概述”和“要点”两项。"
            f"\n视频标题名称为“{title}”，视频字幕数据如下，立刻开始总结：“{transcript}”"
        )
    )


def count_tokens(prompts: list[dict[str, str]]):
    """根据内容计算 token 数"""

    if BotConfig.Bilibili.openai_model.startswith("gpt-3.5-turbo"):
        tokens_per_message = 4
        tokens_per_name = -1
    elif BotConfig.Bilibili.openai_model.startswith("gpt-4"):
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise ValueError(f"Unknown model name {BotConfig.Bilibili.openai_model}")

    num_tokens = 0
    for message in prompts:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(tiktoken_enc.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


def get_small_size_transcripts(text_data: list[str], token_limit: int = LIMIT_COUNT):
    unique_texts = list(OrderedDict.fromkeys(text_data))
    while count_tokens(get_summarise_prompt("", " ".join(unique_texts))) > token_limit:
        unique_texts.pop(random.randint(0, len(unique_texts) - 1))
    return " ".join(unique_texts)


def get_full_prompt(prompt: Optional[str] = None, system: Optional[str] = None, language: Optional[str] = None):
    plist: list[dict[str, str]] = []
    if system:
        plist.append({"role": "system", "content": system})
    if prompt:
        plist.append({"role": "user", "content": prompt})
    if language:
        plist.extend(
            (
                {
                    "role": "assistant",
                    "content": "What language do you want to output?",
                },
                {"role": "user", "content": language},
            )
        )
    if not plist:
        raise ValueError("No prompt provided")
    return plist


async def openai_req(
    prompt_message: list[dict[str, str]],
    token: Optional[str] = BotConfig.Bilibili.openai_api_token,
    model: str = BotConfig.Bilibili.openai_model,
    temperature: Optional[float] = None,
) -> OpenAI:
    if not token:
        logger.warning("未配置 OpenAI API Token，无法总结")
        return OpenAI(error=True, message="未配置 OpenAI API Token")
    async with httpx.AsyncClient(
        proxies=BotConfig.Bilibili.openai_proxy,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.69",
        },
        timeout=100,
    ) as client:
        data = {
            "model": model,
            "messages": prompt_message,
        }
        if temperature:
            data["temperature"] = temperature
        try:
            req: Response = await client.post("https://api.openai.com/v1/chat/completions", json=data)
        except Exception as e:
            logger.exception(e)
            return OpenAI(error=True, message=f"OpenAI 请求失败 {type(e)} {e}")
        if req.status_code != 200:
            return OpenAI(error=True, message=req.text, raw=req.json())
        logger.info(f"[OpenAI] Response:\n{req.json()['choices'][0]['message']['content']}")
        usage = req.json()["usage"]
        logger.info(f"[OpenAI] Response 实际 token 消耗: {usage}")
        return OpenAI(
            response=req.json()["choices"][0]["message"]["content"],
            raw=req.json(),
            token_usage=TokenUsage(**usage),
        )
