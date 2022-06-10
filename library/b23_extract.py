import re
import httpx


async def b23_extract(text):
    if "b23.tv" not in text:
        return None
    b23 = re.compile(r"b23.tv\\/(\w+)").search(text)
    if not b23:
        b23 = re.compile(r"b23.tv/(\w+)").search(text)
    try:
        url = f"https://b23.tv/{b23[1]}"
    except TypeError:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, follow_redirects=True)
    return str(resp.url)