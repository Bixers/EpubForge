from __future__ import annotations

from pathlib import Path

from app.core.converter.calibre_adapter import CalibreAdapter


class MobiConverter:
    def __init__(self, calibre_path: str = "") -> None:
        self.adapter = CalibreAdapter(calibre_path)

    def convert(self, source_path: str | Path, output_path: str | Path):
        return self.adapter.convert(source_path, output_path)

