from __future__ import annotations

import os
import threading
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QSize, Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QToolBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import PrimaryPushButton, PushButton, Theme, setTheme, setThemeColor

from app.core.batch.task_manager import TaskManager
from app.error_report import write_error
from app.core.format_detector import is_supported
from app.core.models import AppConfig, ConvertTask
from app.storage.config_service import ConfigService
from app.ui.book_setting_panel import BookSettingPanel
from app.ui.chapter_preview_panel import ChapterPreviewPanel
from app.ui.icons import toolbar_icon
from app.ui.log_panel import LogPanel
from app.ui.style import APP_STYLESHEET
from app.ui.task_table import TaskTable


class ConversionWorker(QObject):
    task_updated = Signal(object)
    failed = Signal(str)
    finished = Signal(object)

    def __init__(self, manager: TaskManager, tasks: list[ConvertTask]) -> None:
        super().__init__()
        self.manager = manager
        self.tasks = tasks
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

    @Slot()
    def run(self) -> None:
        try:
            self.manager.run_tasks(
                self.tasks,
                on_update=lambda task: self.task_updated.emit(task),
                stop_event=self.stop_event,
                pause_event=self.pause_event,
            )
        except BaseException:
            self.failed.emit(traceback.format_exc())
        finally:
            self.finished.emit(self.tasks)

    def pause(self) -> None:
        self.pause_event.set()

    def resume(self) -> None:
        self.pause_event.clear()

    def stop(self) -> None:
        self.stop_event.set()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EpubForge 电子书工坊")
        icon_path = Path(__file__).resolve().parents[1] / "assets" / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1280, 760)
        self.setAcceptDrops(True)

        self.config_service = ConfigService()
        self.config = self.config_service.load()
        self.manager = TaskManager(self.config)
        self.tasks: list[ConvertTask] = []
        self.thread: QThread | None = None
        self.worker: ConversionWorker | None = None
        self.summary_label = QLabel("任务 0 | 等待 0 | 完成 0 | 失败 0")

        self.task_table = TaskTable()
        self.setting_panel = BookSettingPanel()
        self.preview_panel = ChapterPreviewPanel()
        self.log_panel = LogPanel()
        self.setting_panel.apply_requested.connect(self.apply_book_settings)
        self.preview_panel.chapters_changed.connect(self.on_chapters_changed)
        self.task_table.itemSelectionChanged.connect(self.refresh_side_panel)
        self.task_table.import_files_requested.connect(self.import_files)
        self.task_table.import_folder_requested.connect(self.import_folder)

        tabs = QTabWidget()
        tabs.addTab(self.setting_panel, "书籍设置")
        tabs.addTab(self.preview_panel, "章节编辑")
        tabs.addTab(self.log_panel, "日志详情")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.task_table)
        splitter.addWidget(tabs)
        splitter.setSizes([820, 460])
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)
        self._create_toolbar()
        self.statusBar().addPermanentWidget(self.summary_label)
        self.statusBar().showMessage("就绪")
        self.update_summary()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        actions = [
            ("导入", self.import_files, FIF.DOCUMENT, False),
            ("导入文件夹", self.import_folder, FIF.FOLDER_ADD, False),
            ("开始转换", self.start_conversion, FIF.PLAY, True),
            ("暂停", self.pause_conversion, FIF.PAUSE, False),
            ("继续", self.resume_conversion, FIF.PLAY, False),
            ("停止", self.stop_conversion, toolbar_icon("stop"), False),
            ("重试失败", self.retry_failed_tasks, FIF.SYNC, False),
            ("输出目录", self.open_output_dir, FIF.FOLDER, False),
            ("设置", self.open_settings, FIF.SETTING, False),
            ("清理任务", self.clear_tasks, FIF.DELETE, False),
        ]
        for text, slot, icon_key, is_primary in actions:
            button = PrimaryPushButton() if is_primary else PushButton()
            button.setText(text)
            button.setIcon(icon_key)
            button.setIconSize(QSize(18, 18))
            button.setFixedHeight(38)
            button.clicked.connect(slot)
            toolbar.addWidget(button)

    def import_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "导入文件",
            str(Path.home()),
            "Books (*.txt *.mobi *.azw3 *.md *.markdown *.html *.htm)",
        )
        self.add_paths(paths)

    def import_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "导入文件夹", str(Path.home()))
        if not folder:
            return
        paths = [str(path) for path in Path(folder).rglob("*") if path.is_file() and is_supported(path)]
        self.add_paths(paths, base_dir=folder)

    def add_paths(self, paths: list[str], base_dir: str | None = None) -> None:
        errors: list[str] = []
        for raw_path in paths:
            try:
                task = self.manager.create_task(raw_path, base_dir=base_dir)
            except Exception as exc:
                errors.append(f"{raw_path}: {exc}")
                continue
            self.tasks.append(task)
            self.task_table.add_task(task)
        self.update_summary()
        if errors:
            QMessageBox.warning(self, "部分文件未导入", "\n".join(errors[:10]))
        if self.tasks and self.task_table.selected_row() < 0:
            self.task_table.selectRow(0)

    def start_conversion(self) -> None:
        if self.worker is not None:
            return
        self.preview_panel.save_current_chapter()
        pending = [task for task in self.tasks if task.status in {"等待中", "失败", "已取消"}]
        if not pending:
            QMessageBox.information(self, "没有待转换任务", "请先导入文件，或确认任务不是已完成状态。")
            return
        self.thread = QThread(self)
        self.worker = ConversionWorker(self.manager, pending)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.task_updated.connect(self.on_task_updated)
        self.worker.failed.connect(self.on_worker_failed)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def pause_conversion(self) -> None:
        if self.worker:
            self.worker.pause()

    def resume_conversion(self) -> None:
        if self.worker:
            self.worker.resume()

    def stop_conversion(self) -> None:
        if self.worker:
            self.worker.stop()

    def retry_failed_tasks(self) -> None:
        if self.worker is not None:
            return
        retry_tasks = [task for task in self.tasks if task.status == "失败"]
        if not retry_tasks:
            QMessageBox.information(self, "没有失败任务", "当前任务列表中没有可重试的失败任务。")
            return
        for task in retry_tasks:
            task.status = "等待中"
            task.progress = 0
            task.error_message = ""
            task.log("已加入重试队列")
            self.manager.repository.save_task(task)
            row = self._row_for_task(task.id)
            if row >= 0:
                self.task_table.update_task(row, task)
        self.start_conversion()

    def remove_selected_task(self) -> None:
        row = self.task_table.selected_row()
        if row < 0:
            return
        task_id = self.task_table.task_id_at(row)
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.task_table.removeRow(row)
        self.update_summary()
        self.refresh_side_panel()

    def clear_tasks(self) -> None:
        if self.worker is not None:
            QMessageBox.warning(self, "无法清空", "转换运行中，请先停止任务。")
            return
        self.tasks.clear()
        self.task_table.setRowCount(0)
        self.update_summary()
        self.refresh_side_panel()

    def open_output_dir(self) -> None:
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(output_dir)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config = dialog.to_config()
            self.config_service.save(self.config)
            self.manager.config = self.config
            self.refresh_side_panel()

    @Slot(object)
    def on_task_updated(self, updated: ConvertTask) -> None:
        row = self._row_for_task(updated.id)
        if row >= 0:
            for index, task in enumerate(self.tasks):
                if task.id == updated.id:
                    self.tasks[index] = updated
                    break
            self.task_table.update_task(row, updated)
        self.update_summary()
        self.refresh_side_panel(refresh_preview=False)

    @Slot(object)
    def on_worker_finished(self, finished_tasks: list[ConvertTask]) -> None:
        self.worker = None
        self.thread = None
        completed = sum(1 for task in finished_tasks if task.status == "完成")
        failed = sum(1 for task in finished_tasks if task.status == "失败")
        cancelled = sum(1 for task in finished_tasks if task.status == "已取消")
        QMessageBox.information(
            self,
            "转换完成",
            f"本次任务完成 {completed} 个，失败 {failed} 个，取消 {cancelled} 个。",
        )
        self.update_summary()

    @Slot(str)
    def on_worker_failed(self, error_text: str) -> None:
        path = write_error(error_text)
        QMessageBox.critical(
            self,
            "转换异常",
            f"转换线程发生异常，已写入日志：\n{path}\n\n请保留该日志用于排查。",
        )

    def refresh_side_panel(self, refresh_preview: bool = True) -> None:
        task = self.current_task()
        self.setting_panel.set_task(task)
        if refresh_preview:
            self.preview_panel.set_task(task, self.config)
        self.log_panel.set_log(task.logs if task else [])

    def apply_book_settings(self, values: dict) -> None:
        task = self.current_task()
        if task is None:
            return
        for key, value in values.items():
            setattr(task, key, value)
        task.log("已更新书籍元数据")
        self.manager.repository.save_task(task)
        row = self.task_table.selected_row()
        if row >= 0:
            self.task_table.update_task(row, task)
        self.update_summary()
        self.refresh_side_panel()

    def on_chapters_changed(self, task: ConvertTask) -> None:
        self.manager.repository.save_task(task)
        row = self._row_for_task(task.id)
        if row >= 0:
            self.task_table.update_task(row, task)
        self.update_summary()
        self.log_panel.set_log(task.logs)

    def update_summary(self) -> None:
        total = len(self.tasks)
        waiting = sum(1 for task in self.tasks if task.status == "等待中")
        completed = sum(1 for task in self.tasks if task.status == "完成")
        failed = sum(1 for task in self.tasks if task.status == "失败")
        edited = sum(1 for task in self.tasks if task.has_edited_chapters)
        self.summary_label.setText(
            f"任务 {total} | 等待 {waiting} | 完成 {completed} | 失败 {failed} | 已编辑 {edited}"
        )

    def current_task(self) -> ConvertTask | None:
        row = self.task_table.selected_row()
        if row < 0 or row >= len(self.tasks):
            return None
        task_id = self.task_table.task_id_at(row)
        return next((task for task in self.tasks if task.id == task_id), None)

    def _row_for_task(self, task_id: str) -> int:
        for row in range(self.task_table.rowCount()):
            if self.task_table.task_id_at(row) == task_id:
                return row
        return -1

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt override
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        files: list[str] = []
        for item in paths:
            path = Path(item)
            if path.is_dir():
                files.extend(str(child) for child in path.rglob("*") if child.is_file() and is_supported(child))
            elif path.is_file() and is_supported(path):
                files.append(str(path))
        self.add_paths(files)


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.output_dir_edit = QLineEdit(config.output_dir)
        self.overwrite_check = QCheckBox()
        self.overwrite_check.setChecked(config.overwrite_existing)
        self.keep_structure_check = QCheckBox()
        self.keep_structure_check.setChecked(config.keep_folder_structure)
        self.language_edit = QLineEdit(config.default_language)
        self.author_edit = QLineEdit(config.default_author)
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 16)
        self.concurrency_spin.setValue(config.max_concurrency)
        self.calibre_edit = QLineEdit(config.calibre_path)
        self.chapter_rule_combo = QComboBox()
        self.chapter_rule_combo.addItems(["default", "custom", "fixed_size", "blank_lines", "none"])
        self.chapter_rule_combo.setCurrentText(config.chapter_rule)
        self.custom_regex_edit = QTextEdit()
        self.custom_regex_edit.setPlainText(config.custom_chapter_regex)
        self.custom_regex_edit.setFixedHeight(82)
        self.fixed_chars_spin = QSpinBox()
        self.fixed_chars_spin.setRange(1000, 100000)
        self.fixed_chars_spin.setSingleStep(500)
        self.fixed_chars_spin.setValue(config.fixed_chapter_chars)
        self.default_css_edit = QTextEdit()
        self.default_css_edit.setPlainText(config.default_css)
        self.default_css_edit.setFixedHeight(120)

        browse_output = QPushButton("选择")
        browse_output.clicked.connect(self.choose_output_dir)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_dir_edit)
        output_row.addWidget(browse_output)

        form = QFormLayout()
        form.addRow("默认输出目录", output_row)
        form.addRow("覆盖已有文件", self.overwrite_check)
        form.addRow("保持原文件夹结构", self.keep_structure_check)
        form.addRow("默认语言", self.language_edit)
        form.addRow("默认作者", self.author_edit)
        form.addRow("最大并发任务数", self.concurrency_spin)
        form.addRow("Calibre 路径", self.calibre_edit)
        form.addRow("章节规则", self.chapter_rule_combo)
        form.addRow("自定义章节正则", self.custom_regex_edit)
        form.addRow("固定字数分章", self.fixed_chars_spin)
        form.addRow("默认 CSS 样式", self.default_css_edit)

        ok_button = QPushButton("保存")
        cancel_button = QPushButton("取消")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def choose_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_dir_edit.text())
        if folder:
            self.output_dir_edit.setText(folder)

    def to_config(self) -> AppConfig:
        return AppConfig(
            output_dir=self.output_dir_edit.text().strip(),
            keep_folder_structure=self.keep_structure_check.isChecked(),
            overwrite_existing=self.overwrite_check.isChecked(),
            max_concurrency=self.concurrency_spin.value(),
            default_language=self.language_edit.text().strip() or "zh-CN",
            default_author=self.author_edit.text().strip(),
            chapter_rule=self.chapter_rule_combo.currentText(),
            custom_chapter_regex=self.custom_regex_edit.toPlainText().strip(),
            fixed_chapter_chars=self.fixed_chars_spin.value(),
            calibre_path=self.calibre_edit.text().strip(),
            default_css=self.default_css_edit.toPlainText(),
        )


def run_app() -> int:
    app = QApplication([])
    app.setFont(QFont("Microsoft YaHei UI", 9))
    setTheme(Theme.LIGHT)
    setThemeColor("#1463ff")
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()
