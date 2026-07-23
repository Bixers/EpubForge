from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def error_log_path() -> Path:
    base = os.environ.get("APPDATA")
    root = Path(base) / "EpubForge" if base else Path.home() / ".epubforge"
    root.mkdir(parents=True, exist_ok=True)
    return root / "crash.log"


def write_error(message: str) -> Path:
    path = error_log_path()
    with path.open("a", encoding="utf-8") as file:
        file.write(message.rstrip() + "\n\n")
    return path


def install_exception_hook() -> None:
    def hook(exc_type, exc_value, exc_traceback) -> None:
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        write_error(text)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = hook
