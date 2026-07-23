from __future__ import annotations

import re
from pathlib import Path

try:
    from charset_normalizer import from_bytes
except ImportError:  # pragma: no cover - exercised only without optional dependency
    from_bytes = None

from app.core.chapter.chapter_detector import ChapterDetector
from app.core.models import BookDocument


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
        if raw.startswith(b"\xef\xbb\xbf"):
            return raw.decode("utf-8-sig"), "utf-8-sig"
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            return raw.decode("utf-16"), "utf-16"

        try:
            return raw.decode("utf-8"), "utf-8"
        except UnicodeDecodeError:
            pass

        candidates: list[tuple[str, str]] = []
        for encoding in ("gb18030", "gbk", "big5", "big5hkscs"):
            try:
                candidates.append((raw.decode(encoding), encoding))
            except UnicodeDecodeError:
                continue

        if from_bytes is not None:
            result = from_bytes(raw).best()
            if result is not None and result.encoding:
                candidates.append((str(result), result.encoding))

        if candidates:
            return max(candidates, key=lambda item: self._readability_score(item[0]))

        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5"):
            try:
                return raw.decode(encoding), encoding
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace"), "utf-8-replace"

    def _readability_score(self, text: str) -> int:
        cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
        ascii_printable = sum(1 for char in text if char in "\n\t\r" or " " <= char <= "~")
        punctuation = sum(1 for char in text if char in "，。！？；：“”‘’、（）《》")
        suspicious = sum(
            1
            for char in text
            if char == "\ufffd"
            or "\u2e80" <= char <= "\u2eff"
            or "\ue000" <= char <= "\uf8ff"
        )
        return cjk * 4 + punctuation * 2 + ascii_printable - suspicious * 8

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\ufeff", "")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        return text.strip()
