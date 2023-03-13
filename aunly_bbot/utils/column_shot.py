from lxml import etree
from lxml.etree import _Element, _ElementUnicodeResult

from .bilibili_request import hc
from .detect_package import is_full

XPATH = "//p//text() | //h1/text() | //h2/text() | //h3/text() | //h4/text() | //h5/text() | //h6/text()"


async def get_cv(cvid: str) -> bytes | str | None:
    return await get_cv_screenshot(cvid) if is_full else await get_cv_text(cvid)


async def get_cv_text(cvid: str) -> str:
    cv = await hc.get(f"https://www.bilibili.com/read/cv{cvid}")
    cv.encoding = "utf-8"
    cv = cv.text

    http_parser: _Element = etree.fromstring(cv, etree.HTMLParser(encoding="utf-8"))
    main_article: _Element = http_parser.xpath('//div[@id="read-article-holder"]')[0]
    plist: _ElementUnicodeResult = main_article.xpath(XPATH)
    text_list = [text.strip() for text in plist if text.strip()]
    return "\n".join(text_list)


async def get_cv_screenshot(cvid: str) -> bytes | None:
    from .browser_shot import browser_column

    return await browser_column(cvid)
