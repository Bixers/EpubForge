from __future__ import annotations

from pathlib import Path


SUPPORTED_FORMATS = {
    ".txt": "txt",
    ".mobi": "mobi",
    ".azw3": "azw3",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
}


def detect_format(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"不支持的文件格式：{suffix or '无扩展名'}")
    return SUPPORTED_FORMATS[suffix]


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_FORMATS
