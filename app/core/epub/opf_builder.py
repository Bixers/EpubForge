from __future__ import annotations

from html import escape
from uuid import uuid4

from app.core.models import BookDocument


def build_opf(document: BookDocument, cover_media_type: str = "") -> str:
    identifier = document.metadata.get("identifier") or f"urn:uuid:{uuid4()}"
    keywords = "".join(
        f"    <dc:subject>{escape(item.strip())}</dc:subject>\n"
        for item in document.keywords.split(",")
        if item.strip()
    )
    publisher = (
        f"    <dc:publisher>{escape(document.publisher)}</dc:publisher>\n"
        if document.publisher
        else ""
    )
    description = (
        f"    <dc:description>{escape(document.description)}</dc:description>\n"
        if document.description
        else ""
    )
    cover_item = ""
    cover_meta = ""
    if cover_media_type:
        cover_item = '    <item id="cover-image" href="images/cover%s" media-type="%s" properties="cover-image"/>\n' % (
            _cover_suffix(cover_media_type),
            cover_media_type,
        )
        cover_meta = '    <meta name="cover" content="cover-image"/>\n'

    chapter_items = "\n".join(
        f'    <item id="chapter{chapter.index:03d}" href="chapters/chapter{chapter.index:03d}.xhtml" media-type="application/xhtml+xml"/>'
        for chapter in document.chapters
    )
    spine_items = "\n".join(
        f'    <itemref idref="chapter{chapter.index:03d}"/>' for chapter in document.chapters
    )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="book-id" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{escape(identifier)}</dc:identifier>
    <dc:title>{escape(document.title)}</dc:title>
    <dc:creator>{escape(document.author)}</dc:creator>
    <dc:language>{escape(document.language)}</dc:language>
{publisher}{description}{keywords}{cover_meta}  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="style" href="styles/style.css" media-type="text/css"/>
{cover_item}{chapter_items}
  </manifest>
  <spine>
{spine_items}
  </spine>
</package>
"""


def _cover_suffix(media_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }.get(media_type, ".jpg")

