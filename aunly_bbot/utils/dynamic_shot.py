from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicItem

from ..core.bot_config import BotConfig

from .detect_package import is_full


async def get_dynamic_screenshot(dyn: DynamicItem):
    if is_full and BotConfig.Bilibili.use_browser:
        from .browser_shot import browser_dynamic

        return await browser_dynamic(dyn.extend.dyn_id_str)
    else:
        from .pil_shot import pil_dynamic

        return await pil_dynamic(dyn)
