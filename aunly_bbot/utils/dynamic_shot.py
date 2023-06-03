from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicItem

from ..core.bot_config import BotConfig

from .pil_shot import pil_dynamic
from .detect_package import is_full


async def get_dynamic_screenshot(dyn: DynamicItem):
    if not is_full or not BotConfig.Bilibili.use_browser:
        return await pil_dynamic(dyn)

    from .browser_shot import browser_dynamic

    return (
        await browser_dynamic(dyn.extend.dyn_id_str) or await pil_dynamic(dyn)
        if BotConfig.Bilibili.allow_fallback
        else None
    )
