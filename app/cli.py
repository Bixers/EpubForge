from __future__ import annotations

import argparse
from pathlib import Path

from app.core.batch.task_manager import TaskManager
from app.core.models import AppConfig
from app.storage.task_repository import TaskRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpubForge command line converter")
    parser.add_argument("sources", nargs="+", help="TXT/MOBI/AZW3 source files")
    parser.add_argument("-o", "--output-dir", default="", help="Output directory")
    parser.add_argument("--author", default="", help="Default author")
    parser.add_argument("--language", default="zh-CN", help="Book language")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing EPUB files")
    parser.add_argument("--chapter-rule", default="default", help="default/custom/fixed_size/blank_lines/none")
    parser.add_argument("--custom-chapter-regex", default="", help="Custom chapter title regex")
    parser.add_argument("--fixed-chapter-chars", type=int, default=6000, help="Characters per chapter")
    parser.add_argument("--calibre-path", default="", help="Calibre path or ebook-convert executable")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = args.output_dir or str(Path.cwd() / "output")
    config = AppConfig(
        output_dir=output_dir,
        overwrite_existing=args.overwrite,
        default_author=args.author,
        default_language=args.language,
        chapter_rule=args.chapter_rule,
        custom_chapter_regex=args.custom_chapter_regex,
        fixed_chapter_chars=args.fixed_chapter_chars,
        calibre_path=args.calibre_path,
    )
    manager = TaskManager(config, TaskRepository(Path(output_dir) / "epubforge_tasks.sqlite3"))
    tasks = [manager.create_task(source) for source in args.sources]
    manager.run_tasks(tasks)
    failed = [task for task in tasks if task.status != "完成"]
    for task in tasks:
        print(f"{task.status}: {task.source_path} -> {task.output_path}")
        if task.error_message:
            print(f"  {task.error_message}")
    return 1 if failed else 0
