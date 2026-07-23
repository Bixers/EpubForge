from __future__ import annotations

from pathlib import Path


SUPPORTED_FORMATS = {".txt", ".mobi", ".azw3"}


def detect_format(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"不支持的文件格式：{suffix or '无扩展名'}")
    return suffix.lstrip(".")


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_FORMATS

