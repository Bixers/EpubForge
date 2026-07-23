from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

from app.core.converter.calibre_adapter import CalibreAdapter
from app.core.epub.epub_builder import EpubBuilder
from app.core.epub.validator import EpubValidator
from app.core.format_detector import detect_format
from app.core.models import AppConfig, ConvertTask, now_text
from app.core.parser.txt_parser import TxtParser
from app.core.path_utils import ensure_unique_path, safe_filename
from app.storage.task_repository import TaskRepository


TaskCallback = Callable[[ConvertTask], None]


class TaskCancelled(Exception):
    pass


class TaskManager:
    def __init__(self, config: AppConfig, repository: TaskRepository | None = None) -> None:
        self.config = config
        self.repository = repository or TaskRepository()
        self.validator = EpubValidator()

    def create_task(self, source_path: str | Path, base_dir: str | Path | None = None) -> ConvertTask:
        source = Path(source_path)
        source_format = detect_format(source)
        output_dir = self._task_output_dir(source, Path(base_dir) if base_dir else None)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_name = f"{safe_filename(source.stem)}.epub"
        output_path = self._resolve_output_path(output_dir / output_name)
        task = ConvertTask(
            source_path=source,
            output_path=output_path,
            source_format=source_format,
            file_size=source.stat().st_size if source.exists() else 0,
            author=self.config.default_author,
            language=self.config.default_language,
        )
        task.log(f"已创建任务：{source}")
        self.repository.save_task(task)
        return task

    def run_tasks(
        self,
        tasks: list[ConvertTask],
        on_update: TaskCallback | None = None,
        stop_event: threading.Event | None = None,
        pause_event: threading.Event | None = None,
    ) -> None:
        stop_event = stop_event or threading.Event()
        pause_event = pause_event or threading.Event()
        with ThreadPoolExecutor(max_workers=max(1, self.config.max_concurrency)) as executor:
            futures = {
                executor.submit(self.convert_task, task, on_update, stop_event, pause_event): task
                for task in tasks
                if task.status in {"等待中", "失败", "已取消"}
            }
            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                except Exception as exc:  # ConvertTask should catch its own errors; keep queue fail-open.
                    task.status = "失败"
                    task.error_message = str(exc)
                    task.finished_at = now_text()
                    task.log(f"任务异常结束：{exc}")
                    self._persist_and_emit(task, on_update)

    def convert_task(
        self,
        task: ConvertTask,
        on_update: TaskCallback | None = None,
        stop_event: threading.Event | None = None,
        pause_event: threading.Event | None = None,
    ) -> None:
        stop_event = stop_event or threading.Event()
        pause_event = pause_event or threading.Event()
        if stop_event.is_set():
            self._cancel_task(task, on_update)
            return

        try:
            self._wait_if_paused(pause_event, stop_event)
            task.started_at = now_text()
            task.finished_at = ""
            task.error_message = ""
            task.progress = 3
            task.log(f"源文件路径：{task.source_path}")
            task.log(f"输入文件格式：{task.source_format}")
            self._set_status(task, "解析中", 10, on_update)
            task.output_path = self._resolve_output_path(task.output_path)
            task.log(f"输出文件路径：{task.output_path}")

            if task.source_format == "txt":
                self._convert_txt(task, on_update, stop_event, pause_event)
            elif task.source_format in {"mobi", "azw3"}:
                self._convert_with_calibre(task, on_update, stop_event, pause_event)
            else:
                raise ValueError(f"不支持的文件格式：{task.source_format}")

            if stop_event.is_set():
                self._cancel_task(task, on_update)
                return

            self._set_status(task, "校验中", 92, on_update)
            ok, errors = self.validator.validate(task.output_path)
            if not ok:
                raise ValueError("；".join(errors))
            task.status = "完成"
            task.progress = 100
            task.finished_at = now_text()
            task.log("转换完成")
            self._persist_and_emit(task, on_update)
        except TaskCancelled:
            self._cancel_task(task, on_update)
        except Exception as exc:
            task.status = "失败"
            task.progress = 100
            task.error_message = str(exc)
            task.finished_at = now_text()
            if "drm" in str(exc).lower():
                task.error_message = "该文件可能受 DRM 保护，无法转换。"
            task.log(f"转换失败：{task.error_message}")
            self._persist_and_emit(task, on_update)

    def _convert_txt(
        self,
        task: ConvertTask,
        on_update: TaskCallback | None,
        stop_event: threading.Event,
        pause_event: threading.Event,
    ) -> None:
        self._wait_if_paused(pause_event, stop_event)
        parser = TxtParser(
            self.config.chapter_rule,
            self.config.custom_chapter_regex,
            self.config.fixed_chapter_chars,
        )
        document = parser.parse(
            task.source_path,
            title=task.display_title,
            author=task.author,
            language=task.language,
            publisher=task.publisher,
            description=task.description,
            keywords=task.keywords,
            cover_path=task.cover_path,
        )
        task.log(f"识别编码：{document.metadata.get('source_encoding', 'unknown')}")
        task.log(f"识别章节数：{len(document.chapters)}")
        self._set_status(task, "清洗中", 35, on_update)
        self._wait_if_paused(pause_event, stop_event)
        self._set_status(task, "生成目录中", 55, on_update)
        self._wait_if_paused(pause_event, stop_event)
        self._set_status(task, "生成 EPUB 中", 75, on_update)
        EpubBuilder().build(document, task.output_path, self.config.default_css)

    def _convert_with_calibre(
        self,
        task: ConvertTask,
        on_update: TaskCallback | None,
        stop_event: threading.Event,
        pause_event: threading.Event,
    ) -> None:
        self._wait_if_paused(pause_event, stop_event)
        self._set_status(task, "生成 EPUB 中", 40, on_update)
        adapter = CalibreAdapter(self.config.calibre_path)
        return_code, stdout, stderr, command = adapter.convert(task.source_path, task.output_path)
        task.log("外部工具命令：" + " ".join(f'"{part}"' if " " in part else part for part in command))
        task.log(f"外部工具返回码：{return_code}")
        if stdout.strip():
            task.log("外部工具输出：" + stdout.strip())
        if stderr.strip():
            task.log("外部工具错误：" + stderr.strip())
        if return_code != 0:
            raise RuntimeError(stderr.strip() or stdout.strip() or f"ebook-convert 返回码 {return_code}")

    def _set_status(
        self,
        task: ConvertTask,
        status: str,
        progress: int,
        on_update: TaskCallback | None,
    ) -> None:
        task.status = status
        task.progress = progress
        task.log(status)
        self._persist_and_emit(task, on_update)

    def _cancel_task(self, task: ConvertTask, on_update: TaskCallback | None) -> None:
        task.status = "已取消"
        task.progress = 100
        task.finished_at = now_text()
        task.log("用户取消任务")
        self._persist_and_emit(task, on_update)

    def _wait_if_paused(self, pause_event: threading.Event, stop_event: threading.Event) -> None:
        while pause_event.is_set() and not stop_event.is_set():
            stop_event.wait(0.2)
        if stop_event.is_set():
            raise TaskCancelled()

    def _persist_and_emit(self, task: ConvertTask, on_update: TaskCallback | None) -> None:
        self.repository.save_task(task)
        if on_update:
            on_update(task)

    def _task_output_dir(self, source: Path, base_dir: Path | None) -> Path:
        output_dir = Path(self.config.output_dir)
        if self.config.keep_folder_structure and base_dir is not None:
            try:
                relative_parent = source.parent.relative_to(base_dir)
            except ValueError:
                relative_parent = Path()
            if str(relative_parent) != ".":
                output_dir = output_dir / relative_parent
        return output_dir

    def _resolve_output_path(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if self.config.overwrite_existing:
            return output_path
        return ensure_unique_path(output_path)
