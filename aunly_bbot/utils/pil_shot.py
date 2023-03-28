from io import BytesIO
from pathlib import Path
from minidynamicrender.Core import DyRender
from google.protobuf.json_format import MessageToDict
from dynamicadaptor.DynamicConversion import formate_message
from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicItem

from .fonts_provider import get_font


data_path = Path("data", "render")
data_path.mkdir(parents=True, exist_ok=True)


async def pil_dynamic(dyn: DynamicItem):
    dynamic: dict = MessageToDict(dyn)
    dynamic_formate = await formate_message("grpc", dynamic)
    if dynamic_formate:
        img_bio = BytesIO()
        render = DyRender(
            data_path=str(data_path),
            font_path={
                "text": str(await get_font("HarmonyOS_Sans_SC_Medium.ttf")),
                "extra_text": str(await get_font("sarasa-mono-sc-bold.ttf")),
                "emoji": str(await get_font("nte.ttf")),
            },
        )
        dynamic_render = await render.dyn_render(dynamic_formate)
        dynamic_render.convert("RGB").save(img_bio, "jpeg", optimize=True)
        return img_bio.getvalue()
