from __future__ import annotations

import re

from app.core.chapter.rules import DEFAULT_CHAPTER_RULES, compile_rule_patterns, is_volume_title
from app.core.models import Chapter


DEFAULT_CHAPTER_REGEX = DEFAULT_CHAPTER_RULES[0].pattern


class ChapterDetector:
    def __init__(
        self,
        rule: str = "default",
        custom_regex: str = "",
        fixed_chars: int = 6000,
    ) -> None:
        self.rule = rule or "default"
        self.custom_regex = custom_regex
        self.fixed_chars = max(1000, fixed_chars)

    def detect(self, text: str) -> list[Chapter]:
        if self.rule == "none":
            return [Chapter(1, "正文", text.strip())]
        if self.rule == "fixed_size":
            return self._by_fixed_size(text)
        if self.rule == "blank_lines":
            return self._by_blank_lines(text)
        pattern = self.custom_regex if self.rule == "custom" else DEFAULT_CHAPTER_REGEX
        return self._by_heading(text, pattern)

    def _by_heading(self, text: str, pattern: str) -> list[Chapter]:
        patterns = compile_rule_patterns(self.custom_regex) if self.rule != "custom" else [
            re.compile(item, re.IGNORECASE) for item in [pattern] if item
        ]
        chapters: list[Chapter] = []
        current_volume = ""
        current_title = "正文"
        current_lines: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            is_title = bool(stripped and any(regex.match(stripped) for regex in patterns))
            if stripped == "正文" and self._is_numbered_chapter_title(current_title):
                is_title = False

            if is_title:
                if is_volume_title(stripped):
                    if current_lines or current_title != "正文":
                        chapters.append(
                            Chapter(
                                len(chapters) + 1,
                                current_title,
                                "\n".join(current_lines).strip(),
                                volume_title=current_volume,
                            )
                        )
                    current_volume = stripped
                    current_title = "正文"
                    current_lines = []
                    continue
                if current_lines or current_title != "正文":
                    chapters.append(
                        Chapter(
                            len(chapters) + 1,
                            current_title,
                            "\n".join(current_lines).strip(),
                            volume_title=current_volume,
                        )
                    )
                current_title = stripped
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines or not chapters:
            chapters.append(
                Chapter(
                    len(chapters) + 1,
                    current_title,
                    "\n".join(current_lines).strip(),
                    volume_title=current_volume,
                )
            )

        return [chapter for chapter in chapters if chapter.content or chapter.title]

    def _is_numbered_chapter_title(self, title: str) -> bool:
        numbered_patterns = [
            r"^第[一二三四五六七八九十百千万两0-9]+[章节回卷部].*$",
            r"^[卷部][一二三四五六七八九十百千万两0-9]+.*$",
            r"^[0-9]{1,4}[\.．、]\s*.+$",
            r"^(章节?\s*)?[0-9]{1,4}\s+.+$",
            r"^(chapter|part|volume|book)\s+[0-9ivxlcdm]+[:\.\-\s].*$",
        ]
        return any(re.match(pattern, title, re.IGNORECASE) for pattern in numbered_patterns)

    def _by_fixed_size(self, text: str) -> list[Chapter]:
        cleaned = text.strip()
        if not cleaned:
            return [Chapter(1, "正文", "")]
        chapters: list[Chapter] = []
        for start in range(0, len(cleaned), self.fixed_chars):
            index = len(chapters) + 1
            chapters.append(Chapter(index, f"第 {index} 章", cleaned[start : start + self.fixed_chars]))
        return chapters

    def _by_blank_lines(self, text: str) -> list[Chapter]:
        parts = [part.strip() for part in re.split(r"\n\s*\n\s*\n+", text) if part.strip()]
        if not parts:
            return [Chapter(1, "正文", text.strip())]
        return [Chapter(index + 1, f"第 {index + 1} 章", part) for index, part in enumerate(parts)]
