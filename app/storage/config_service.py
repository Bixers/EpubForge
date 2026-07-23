from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.core.models import AppConfig


class ConfigService:
    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else self.default_config_path()

    def default_config_path(self) -> Path:
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "EpubForge" / "config.json"
        return Path.home() / ".epubforge" / "config.json"

    def load(self) -> AppConfig:
        default = self.default_config()
        if not self.config_path.exists():
            self.save(default)
            return default
        try:
            data: dict[str, Any] = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default
        merged = asdict(default)
        merged.update({key: value for key, value in data.items() if key in merged})
        return AppConfig(**merged)

    def save(self, config: AppConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def default_config(self) -> AppConfig:
        public_dir = os.environ.get("PUBLIC")
        if public_dir:
            output_dir = Path(public_dir) / "Documents" / "EpubForge"
        else:
            output_dir = Path.home() / "Documents" / "EpubForge"
        return AppConfig(output_dir=str(output_dir))

