from __future__ import annotations

import re
from pathlib import Path


INVALID_FILENAME_CHARS = r'<>:"/\|?*'


def safe_filename(name: str, replacement: str = "_") -> str:
    cleaned = "".join(replacement if ch in INVALID_FILENAME_CHARS else ch for ch in name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or "untitled"


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1

