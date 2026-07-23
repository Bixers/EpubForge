from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass(slots=True)
class Chapter:
    index: int
    title: str
    content: str
    content_format: str = "text"
    volume_title: str = ""


@dataclass(slots=True)
class BookDocument:
    title: str
    author: str = ""
    language: str = "zh-CN"
    publisher: str = ""
    description: str = ""
    keywords: str = ""
    cover_path: str = ""
    chapters: list[Chapter] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AppConfig:
    output_dir: str
    keep_folder_structure: bool = False
    overwrite_existing: bool = False
    max_concurrency: int = 2
    default_language: str = "zh-CN"
    default_author: str = ""
    chapter_rule: str = "default"
    custom_chapter_regex: str = ""
    fixed_chapter_chars: int = 6000
    calibre_path: str = ""
    default_css: str = ""


@dataclass(slots=True)
class ConvertTask:
    source_path: Path
    output_path: Path
    source_format: str
    id: str = field(default_factory=lambda: f"task-{uuid4().hex[:12]}")
    status: str = "等待中"
    progress: int = 0
    error_message: str = ""
    file_size: int = 0
    title: str = ""
    author: str = ""
    language: str = "zh-CN"
    publisher: str = ""
    description: str = ""
    keywords: str = ""
    cover_path: str = ""
    created_at: str = field(default_factory=now_text)
    started_at: str = ""
    finished_at: str = ""
    logs: list[str] = field(default_factory=list)
    edited_chapters: list[Chapter] = field(default_factory=list)

    def log(self, message: str) -> None:
        self.logs.append(f"[{now_text()}] {message}")

    @property
    def display_title(self) -> str:
        return self.title.strip() or self.source_path.stem

    @property
    def has_edited_chapters(self) -> bool:
        return bool(self.edited_chapters)
