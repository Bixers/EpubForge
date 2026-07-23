from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class CalibreAdapter:
    def __init__(self, calibre_path: str = "") -> None:
        self.calibre_path = calibre_path

    def find_executable(self) -> str:
        if self.calibre_path:
            candidate = Path(self.calibre_path)
            if candidate.is_dir():
                candidate = candidate / "ebook-convert.exe"
            if candidate.exists():
                return str(candidate)
        found = shutil.which("ebook-convert") or shutil.which("ebook-convert.exe")
        if found:
            return found
        raise FileNotFoundError("未找到 Calibre ebook-convert，请在设置中配置 Calibre 路径")

    def convert(self, source_path: str | Path, output_path: str | Path) -> tuple[int, str, str, list[str]]:
        executable = self.find_executable()
        command = [executable, str(source_path), str(output_path)]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return completed.returncode, completed.stdout, completed.stderr, command

