from __future__ import annotations

import mimetypes
import zipfile
from html import escape
from pathlib import Path

from app.core.epub.nav_builder import build_nav
from app.core.epub.opf_builder import build_opf
from app.core.models import BookDocument, Chapter


DEFAULT_CSS = """body {
  font-family: "Microsoft YaHei", "Noto Serif CJK SC", serif;
  line-height: 1.8;
  margin: 1.2em;
}
h1 {
  font-size: 1.6em;
  margin-bottom: 1.2em;
}
p {
  text-indent: 2em;
  margin: 0.4em 0;
}
"""


class EpubBuilder:
    def build(self, document: BookDocument, output_path: str | Path, css: str = "") -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        cover_source, cover_media_type, cover_name = self._cover_info(document.cover_path)

        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr(
                zipfile.ZipInfo("mimetype"),
                "application/epub+zip",
                compress_type=zipfile.ZIP_STORED,
            )
            archive.writestr("META-INF/container.xml", self._container_xml())
            archive.writestr("OEBPS/styles/style.css", css or DEFAULT_CSS)
            archive.writestr("OEBPS/nav.xhtml", build_nav(document))
            archive.writestr("OEBPS/content.opf", build_opf(document, cover_media_type))
            if cover_source and cover_name:
                archive.write(cover_source, f"OEBPS/images/{cover_name}")
            for chapter in document.chapters:
                archive.writestr(
                    f"OEBPS/chapters/chapter{chapter.index:03d}.xhtml",
                    self._chapter_xhtml(document, chapter),
                )
        return output

    def _container_xml(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    def _chapter_xhtml(self, document: BookDocument, chapter: Chapter) -> str:
        body = self._chapter_body(chapter)
        return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{escape(document.language)}">
<head>
  <meta charset="utf-8"/>
  <title>{escape(chapter.title)}</title>
  <link rel="stylesheet" type="text/css" href="../styles/style.css"/>
</head>
<body>
  <h1>{escape(chapter.title)}</h1>
{body}
</body>
</html>
"""

    def _chapter_body(self, chapter: Chapter) -> str:
        if chapter.content_format == "xhtml":
            return chapter.content.strip() or "  <p></p>"
        paragraphs = []
        for paragraph in chapter.content.splitlines():
            stripped = paragraph.strip()
            if stripped:
                paragraphs.append(f"  <p>{escape(stripped)}</p>")
        return "\n".join(paragraphs) or "  <p></p>"

    def _cover_info(self, cover_path: str) -> tuple[Path | None, str, str]:
        if not cover_path:
            return None, "", ""
        source = Path(cover_path)
        if not source.exists():
            raise FileNotFoundError(f"封面图片不存在：{source}")
        media_type = mimetypes.guess_type(source.name)[0] or "image/jpeg"
        suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }.get(media_type, source.suffix.lower() or ".jpg")
        return source, media_type, f"cover{suffix}"
