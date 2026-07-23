from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from pathlib import Path

from app.core.models import ConvertTask


class TaskRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else self.default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def default_db_path(self) -> Path:
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "EpubForge" / "tasks.sqlite3"
        return Path.home() / ".epubforge" / "tasks.sqlite3"

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS convert_tasks (
                        id TEXT PRIMARY KEY,
                        source_path TEXT NOT NULL,
                        output_path TEXT NOT NULL,
                        source_format TEXT NOT NULL,
                        status TEXT NOT NULL,
                        progress INTEGER NOT NULL,
                        error_message TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        finished_at TEXT,
                        logs TEXT NOT NULL
                    )
                    """
                )
                existing_columns = {
                    row[1] for row in conn.execute("PRAGMA table_info(convert_tasks)").fetchall()
                }
                for column_name, column_type in {
                    "title": "TEXT NOT NULL DEFAULT ''",
                    "author": "TEXT NOT NULL DEFAULT ''",
                    "language": "TEXT NOT NULL DEFAULT 'zh-CN'",
                    "publisher": "TEXT NOT NULL DEFAULT ''",
                    "description": "TEXT NOT NULL DEFAULT ''",
                    "keywords": "TEXT NOT NULL DEFAULT ''",
                    "cover_path": "TEXT NOT NULL DEFAULT ''",
                }.items():
                    if column_name not in existing_columns:
                        conn.execute(
                            f"ALTER TABLE convert_tasks ADD COLUMN {column_name} {column_type}"
                        )

    def save_task(self, task: ConvertTask) -> None:
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO convert_tasks (
                        id, source_path, output_path, source_format, status, progress,
                        error_message, created_at, started_at, finished_at, logs,
                        title, author, language, publisher, description, keywords, cover_path
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        output_path = excluded.output_path,
                        status = excluded.status,
                        progress = excluded.progress,
                        error_message = excluded.error_message,
                        started_at = excluded.started_at,
                        finished_at = excluded.finished_at,
                        logs = excluded.logs,
                        title = excluded.title,
                        author = excluded.author,
                        language = excluded.language,
                        publisher = excluded.publisher,
                        description = excluded.description,
                        keywords = excluded.keywords,
                        cover_path = excluded.cover_path
                    """,
                    (
                        task.id,
                        str(task.source_path),
                        str(task.output_path),
                        task.source_format,
                        task.status,
                        task.progress,
                        task.error_message,
                        task.created_at,
                        task.started_at,
                        task.finished_at,
                        "\n".join(task.logs),
                        task.title,
                        task.author,
                        task.language,
                        task.publisher,
                        task.description,
                        task.keywords,
                        task.cover_path,
                    ),
                )
