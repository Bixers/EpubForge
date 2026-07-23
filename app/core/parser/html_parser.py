from __future__ import annotations

import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path

from app.core.models import BookDocument, Chapter
from app.core.chapter.rules import is_volume_title
from app.core.parser.text_decoder import decode_text_file


class _HtmlChapterExtractor(HTMLParser):
    BLOCK_TAGS = {"p", "div", "section", "article", "blockquote"}
    HEADING_TAGS = {"h1", "h2"}
    INLINE_TAGS = {
        "strong": "strong",
        "b": "strong",
        "em": "em",
        "i": "em",
        "code": "code",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.chapters: list[Chapter] = []
        self.current_volume = ""
        self.current_title = "正文"
        self.current_blocks: list[str] = []
        self.current_text: list[str] = []
        self.current_tag = ""
        self.title_depth = 0
        self.skip_depth = 0
        self.list_stack: list[list[str]] = []
        self.inline_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.title_depth += 1
            return
        if tag in self.HEADING_TAGS:
            self._flush_text_block()
            self.current_tag = tag
            self.current_text = []
            return
        if tag in self.BLOCK_TAGS or tag == "pre":
            self._flush_text_block()
            self.current_tag = tag
            self.current_text = []
            return
        if tag in {"ul", "ol"}:
            self._flush_text_block()
            self.list_stack.append([])
            return
        if tag == "li":
            self.current_tag = tag
            self.current_text = []
            return
        if tag in self.INLINE_TAGS:
            if not self.current_tag:
                self.current_tag = "p"
                self.current_text = []
            self.inline_stack.append(self.INLINE_TAGS[tag])
            self.current_text.append(f"<{self.INLINE_TAGS[tag]}>")
            return
        if tag == "br":
            self.current_text.append("<br/>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
            return
        if tag in self.INLINE_TAGS and self.inline_stack:
            current = self.inline_stack.pop()
            self.current_text.append(f"</{current}>")
            return
        if tag in self.HEADING_TAGS and self.current_tag == tag:
            heading = self._plain_current_text()
            if heading:
                if tag == "h1" and is_volume_title(heading):
                    if self.current_blocks or self.current_title != "正文":
                        self._append_chapter()
                    self.current_volume = heading
                    self.current_title = "正文"
                    self.current_tag = ""
                    self.current_text = []
                    return
                if self.current_blocks or self.current_title != "正文":
                    self._append_chapter()
                self.current_title = heading
            self.current_tag = ""
            self.current_text = []
            return
        if tag in self.BLOCK_TAGS and self.current_tag == tag:
            self._flush_text_block()
            return
        if tag == "pre" and self.current_tag == tag:
            value = "".join(self.current_text).strip()
            if value:
                self.current_blocks.append(f"  <pre><code>{value}</code></pre>")
            self.current_tag = ""
            self.current_text = []
            return
        if tag == "li" and self.current_tag == tag:
            value = "".join(self.current_text).strip()
            if value and self.list_stack:
                self.list_stack[-1].append(value)
            self.current_tag = ""
            self.current_text = []
            return
        if tag in {"ul", "ol"} and self.list_stack:
            items = self.list_stack.pop()
            if items:
                xhtml_items = "\n".join(f"    <li>{item}</li>" for item in items)
                self.current_blocks.append(f"  <{tag}>\n{xhtml_items}\n  </{tag}>")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.title_depth:
            self.title += data
            return
        if not self.current_tag and data.strip():
            self.current_tag = "p"
            self.current_text = []
        if self.current_tag:
            self.current_text.append(escape(data))

    def close(self) -> None:
        super().close()
        self._flush_text_block()
        if self.current_blocks or not self.chapters:
            self._append_chapter()

    def _flush_text_block(self) -> None:
        if not self.current_tag:
            return
        value = "".join(self.current_text).strip()
        if value:
            wrapper = "blockquote" if self.current_tag == "blockquote" else "p"
            self.current_blocks.append(f"  <{wrapper}>{value}</{wrapper}>")
        self.current_tag = ""
        self.current_text = []

    def _plain_current_text(self) -> str:
        text = re.sub(r"<[^>]+>", "", "".join(self.current_text))
        return text.strip()

    def _append_chapter(self) -> None:
        content = "\n".join(self.current_blocks) or "  <p></p>"
        self.chapters.append(
            Chapter(len(self.chapters) + 1, self.current_title, content, "xhtml", self.current_volume)
        )
        self.current_blocks = []


class HtmlParser:
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
        extractor = _HtmlChapterExtractor()
        extractor.feed(text)
        extractor.close()
        return BookDocument(
            title=title or extractor.title.strip() or source.stem,
            author=author,
            language=language,
            publisher=publisher,
            description=description,
            keywords=keywords,
            cover_path=cover_path,
            chapters=extractor.chapters,
            metadata={"source_encoding": encoding, "source_path": str(source)},
        )
