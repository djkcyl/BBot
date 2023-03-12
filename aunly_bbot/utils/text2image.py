import asyncio

from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

from .strings import get_cut_str
from .fonts_provider import get_font_sync


font = ImageFont.truetype(str(get_font_sync("sarasa-mono-sc-semibold.ttf")), size=20)


async def text2image(text: str, cut=64) -> bytes:
    return await asyncio.to_thread(_create_image, text, cut)


def _create_image(text: str, cut: int) -> bytes:
    cut_str = "\n".join(get_cut_str(text, cut))
    textx, texty = font.getsize_multiline(cut_str)
    image = Image.new("RGB", (textx + 40, texty + 40), (235, 235, 235))
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), cut_str, font=font, fill=(31, 31, 33))
    imageio = BytesIO()
    image.save(
        imageio,
        format="JPEG",
        quality=90,
        subsampling=2,
        qtables="web_high",
    )
    return imageio.getvalue()
