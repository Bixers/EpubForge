from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChapterRule:
    name: str
    pattern: str
    description: str


DEFAULT_CHAPTER_RULES = [
    ChapterRule("chinese_numbered", r"^第[一二三四五六七八九十百千万两0-9]+[章节回卷部].*$", "第一章 / 第12章 / 第三卷"),
    ChapterRule("chinese_volume", r"^[卷部][一二三四五六七八九十百千万两0-9]+.*$", "卷一 / 部二"),
    ChapterRule("arabic_dot", r"^[0-9]{1,4}[\.．、]\s*.+$", "1. 标题 / 2、标题"),
    ChapterRule("arabic_chapter", r"^(章节?\s*)?[0-9]{1,4}\s+.+$", "1 标题 / 章节 2 标题"),
    ChapterRule("english_chapter", r"^(chapter|part|volume|book)\s+[0-9ivxlcdm]+[:\.\-\s].*$", "Chapter 1 / Part II"),
    ChapterRule("preface_names", r"^(序章|楔子|前言|引子|正文|尾声|后记|番外.*|终章)$", "序章 / 正文 / 后记 / 番外"),
]

VOLUME_RULES = [
    ChapterRule("chinese_volume_numbered", r"^第[一二三四五六七八九十百千万两0-9]+[卷部].*$", "第一卷 / 第二部"),
    ChapterRule("chinese_volume_prefix", r"^[卷部][一二三四五六七八九十百千万两0-9]+.*$", "卷一 / 部二"),
    ChapterRule("english_volume", r"^(volume|part|book)\s+[0-9ivxlcdm]+[:\.\-\s].*$", "Volume 1 / Part II / Book 3"),
]


def compile_rule_patterns(custom_regex: str = "") -> list[re.Pattern[str]]:
    patterns = [rule.pattern for rule in DEFAULT_CHAPTER_RULES]
    for item in split_custom_regex(custom_regex):
        patterns.append(item)
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def split_custom_regex(custom_regex: str) -> list[str]:
    return [item.strip() for item in re.split(r"[\r\n;]+", custom_regex or "") if item.strip()]


def is_volume_title(title: str) -> bool:
    return any(re.match(rule.pattern, title.strip(), re.IGNORECASE) for rule in VOLUME_RULES)
