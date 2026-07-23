from __future__ import annotations

import re
from html import escape
from pathlib import Path

from app.core.models import BookDocument, Chapter
from app.core.parser.text_decoder import decode_text_file


class MarkdownParser:
    def parse(
        self,
        path: str | Path,
        title: str | None = None,
        author: str = "",
        language: str = "zh-CN",
        publisher: str = "",
        description: str = "",
        keywords: str = "",
        cover_path: str = "",
    ) -> BookDocument:
        source = Path(path)
        text, encoding = decode_text_file(source)
        chapters = self._chapters_from_markdown(text)
        return BookDocument(
            title=title or source.stem,
            author=author,
            language=language,
            publisher=publisher,
            description=description,
            keywords=keywords,
            cover_path=cover_path,
            chapters=chapters,
            metadata={"source_encoding": encoding, "source_path": str(source)},
        )

    def _chapters_from_markdown(self, text: str) -> list[Chapter]:
        chapters: list[Chapter] = []
        current_title = "正文"
        current_lines: list[str] = []

        for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
            match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if match and len(match.group(1)) <= 2:
                if current_lines or chapters:
                    chapters.append(self._build_chapter(len(chapters) + 1, current_title, current_lines))
                current_title = match.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)
        if current_lines or not chapters:
            chapters.append(self._build_chapter(len(chapters) + 1, current_title, current_lines))
        return chapters

    def _build_chapter(self, index: int, title: str, lines: list[str]) -> Chapter:
        return Chapter(index, title, self._to_xhtml(lines), "xhtml")

    def _to_xhtml(self, lines: list[str]) -> str:
        blocks: list[str] = []
        paragraph: list[str] = []
        list_items: list[str] = []
        code_lines: list[str] = []
        in_code = False

        def flush_paragraph() -> None:
            if paragraph:
                blocks.append(f"  <p>{self._inline(' '.join(item.strip() for item in paragraph))}</p>")
                paragraph.clear()

        def flush_list() -> None:
            if list_items:
                items = "\n".join(f"    <li>{item}</li>" for item in list_items)
                blocks.append(f"  <ul>\n{items}\n  </ul>")
                list_items.clear()

        def flush_code() -> None:
            if code_lines:
                blocks.append(f"  <pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code:
                    flush_code()
                    in_code = False
                else:
                    flush_paragraph()
                    flush_list()
                    in_code = True
                continue
            if in_code:
                code_lines.append(line)
                continue
            if not stripped:
                flush_paragraph()
                flush_list()
                continue
            heading = re.match(r"^(#{3,6})\s+(.+?)\s*$", stripped)
            if heading:
                flush_paragraph()
                flush_list()
                level = min(6, len(heading.group(1)) + 1)
                blocks.append(f"  <h{level}>{self._inline(heading.group(2))}</h{level}>")
                continue
            item = re.match(r"^[-*+]\s+(.+)$", stripped)
            if item:
                flush_paragraph()
                list_items.append(self._inline(item.group(1)))
                continue
            paragraph.append(line)

        flush_code()
        flush_paragraph()
        flush_list()
        return "\n".join(blocks) or "  <p></p>"

    def _inline(self, text: str) -> str:
        value = escape(text)
        value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
        value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
        value = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", value)
        value = re.sub(
            r"\[([^\]]+)\]\((https?://[^)\"<>\s]+)\)",
            r'<a href="\2">\1</a>',
            value,
        )
        return value
