from __future__ import annotations

import re
from pathlib import Path

from app.core.chapter.chapter_detector import ChapterDetector
from app.core.models import BookDocument
from app.core.parser.text_decoder import decode_bytes


class TxtParser:
    def __init__(
        self,
        chapter_rule: str = "default",
        custom_chapter_regex: str = "",
        fixed_chapter_chars: int = 6000,
    ) -> None:
        self.detector = ChapterDetector(chapter_rule, custom_chapter_regex, fixed_chapter_chars)

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
        raw = source.read_bytes()
        text, encoding = self._decode(raw)
        cleaned = self._clean_text(text)
        chapters = self.detector.detect(cleaned)
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

    def _decode(self, raw: bytes) -> tuple[str, str]:
        return decode_bytes(raw)

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\ufeff", "")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        return text.strip()
