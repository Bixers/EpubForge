from __future__ import annotations

import re

from app.core.models import Chapter


DEFAULT_CHAPTER_REGEX = r"^(第[一二三四五六七八九十百千万0-9]+[章节回卷部].*)$"
EXTRA_TITLE_REGEXES = [
    r"^(序章|楔子|前言|正文|尾声|后记)$",
    r"^(番外.*)$",
    r"^(Chapter\s+\d+.*)$",
]


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
        compiled = re.compile(pattern, re.IGNORECASE)
        extras = [re.compile(item, re.IGNORECASE) for item in EXTRA_TITLE_REGEXES]
        chapters: list[Chapter] = []
        current_title = "正文"
        current_lines: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            is_title = bool(stripped and compiled.match(stripped))
            if not is_title:
                is_title = any(regex.match(stripped) for regex in extras)
            if stripped == "正文" and self._is_numbered_chapter_title(current_title):
                is_title = False

            if is_title:
                if current_lines or chapters or current_title != "正文":
                    chapters.append(
                        Chapter(len(chapters) + 1, current_title, "\n".join(current_lines).strip())
                    )
                current_title = stripped
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines or not chapters:
            chapters.append(
                Chapter(len(chapters) + 1, current_title, "\n".join(current_lines).strip())
            )

        return [chapter for chapter in chapters if chapter.content or chapter.title]

    def _is_numbered_chapter_title(self, title: str) -> bool:
        if re.match(DEFAULT_CHAPTER_REGEX, title, re.IGNORECASE):
            return True
        return bool(re.match(r"^Chapter\s+\d+.*$", title, re.IGNORECASE))

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
