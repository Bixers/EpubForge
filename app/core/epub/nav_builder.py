from __future__ import annotations

from html import escape

from app.core.models import BookDocument


def build_nav(document: BookDocument) -> str:
    items = "\n".join(
        f'      <li><a href="chapters/chapter{chapter.index:03d}.xhtml">{escape(chapter.title)}</a></li>'
        for chapter in document.chapters
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{escape(document.language)}">
<head>
  <meta charset="utf-8"/>
  <title>{escape(document.title)} - 目录</title>
  <link rel="stylesheet" type="text/css" href="styles/style.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>目录</h1>
    <ol>
{items}
    </ol>
  </nav>
</body>
</html>
"""

