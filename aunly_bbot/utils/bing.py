import json
import random
import re
from collections import OrderedDict
from pathlib import Path
from typing import List

from EdgeGPT import Chatbot, ConversationStyle
from loguru import logger
from ..core.bot_config import BotConfig

from ..model.exception import AbortError

cookies = json.loads(Path(BotConfig.Bilibili.newbing_cookie).read_text("utf-8"))  # type: ignore
logger.info("Try init bing chatbot")
for count in range(5):
    try:
        bot = Chatbot(cookies=cookies, proxy=BotConfig.Bilibili.openai_proxy)  # type: ignore
        logger.success("Bing chatbot init success")
        break
    except Exception:
        logger.error(f"Bing chatbot init failed, retrying {count+1}/5")


async def bing_summarise(title: str, text_data: List[str]):
    prompt = f"请为视频“{title}”总结文案,开头简述要点(大于40字符),\
随后总结2-6条视频的Bulletpoint(每条大于15字符),\
然后使用以下格式输出总结内容 ## 总结 \n ## 要点 \n - [Emoji] Bulletpoint\n\n,\
如果你无法找到相关的信息可以尝试自己总结,\
但请一定不要输出任何其他内容。视频文案的内容如下: "
    unique_texts = list(OrderedDict.fromkeys(text_data))
    if BotConfig.Bilibili.newbing_token_limit > 0:
        while (
            len(",".join(unique_texts)) + len(prompt) > BotConfig.Bilibili.newbing_token_limit
        ):
            unique_texts.pop(random.randint(0, len(unique_texts) - 1))
    return await newbing_req(prompt + ",".join(unique_texts))


async def newbing_req(prompt: str):
    logger.debug(f"prompt have {len(prompt)} chars")
    ans = await bot.ask(
        prompt=prompt,
        conversation_style=ConversationStyle.creative,
        wss_link="wss://sydney.bing.com/sydney/ChatHub",
    )
    await bot.reset()
    logger.debug(ans)
    bing_resp = ans["item"]["messages"][1]
    if bing_resp["contentOrigin"] == "Apology":
        raise AbortError("newbing 认为视频或专栏内容包含冒犯性内容")
    elif len(bing_resp["text"]) < 100:
        raise AbortError("newbing 无法总结此内容")
    else:
        return bing_resp["text"]
