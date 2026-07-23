from __future__ import annotations

from html import escape

from app.core.models import BookDocument


def build_nav(document: BookDocument) -> str:
    items = _build_nav_items(document)
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


def _build_nav_items(document: BookDocument) -> str:
    lines: list[str] = []
    current_volume = None
    for chapter in document.chapters:
        volume = chapter.volume_title.strip()
        if volume and volume != current_volume:
            if current_volume is not None:
                lines.append("        </ol>")
                lines.append("      </li>")
            current_volume = volume
            lines.append(f"      <li><span>{escape(volume)}</span>")
            lines.append("        <ol>")
        elif not volume and current_volume is not None:
            lines.append("        </ol>")
            lines.append("      </li>")
            current_volume = None

        indent = "          " if current_volume else "      "
        lines.append(
            f'{indent}<li><a href="chapters/chapter{chapter.index:03d}.xhtml">{escape(chapter.title)}</a></li>'
        )
    if current_volume is not None:
        lines.append("        </ol>")
        lines.append("      </li>")
    return "\n".join(lines)
