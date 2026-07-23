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
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QToolBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)
from qfluentwidgets import CheckBox, ComboBox as FluentComboBox, FluentIcon as FIF
from qfluentwidgets import LineEdit as FluentLineEdit
from qfluentwidgets import PrimaryPushButton, PushButton, SpinBox, TextEdit as FluentTextEdit, Theme, setTheme, setThemeColor

from app.core.batch.task_manager import TaskManager
from app.core.presets import CSS_TEMPLATES, CONVERSION_PRESETS, css_template_names, conversion_preset_names
from app.error_report import write_error
from app.core.format_detector import is_supported
from app.core.models import AppConfig, ConvertTask
from app.storage.config_service import ConfigService
from app.ui.book_setting_panel import BookSettingPanel
from app.ui.chapter_preview_panel import ChapterPreviewPanel
from app.ui.icons import toolbar_icon
from app.ui.log_panel import LogPanel
from app.ui.style import APP_STYLESHEET, apply_light_palette
from app.ui.task_table import TaskTable


def app_icon_path() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "app.ico"


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
        icon_path = app_icon_path()
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
        self.conversion_paused = False
        self.toolbar_buttons: dict[str, PushButton] = {}
        self.summary_label = QLabel("任务 0 | 等待 0 | 完成 0 | 失败 0")
        self.summary_label.setObjectName("summaryLabel")

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
        tabs.setMinimumWidth(320)
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tabs.addTab(self._scrollable_panel(self.setting_panel), "书籍设置")
        tabs.addTab(self._scrollable_panel(self.preview_panel), "章节编辑")
        tabs.addTab(self._scrollable_panel(self.log_panel), "日志详情")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        splitter.addWidget(self.task_table)
        splitter.addWidget(tabs)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([760, 520])
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)
        self._create_toolbar()
        self.statusBar().setFixedHeight(32)
        self.statusBar().addPermanentWidget(self.summary_label)
        self.statusBar().showMessage("就绪")
        self.update_summary()

    def _scrollable_panel(self, panel: QWidget) -> QScrollArea:
        scroll_area = QScrollArea()
        scroll_area.setWidget(panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumWidth(0)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return scroll_area

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        groups = [
            [
                ("import", "导入", self.import_files, FIF.DOCUMENT, False),
                ("import_folder", "导入文件夹", self.import_folder, FIF.FOLDER_ADD, False),
            ],
            [
                ("start", "开始转换", self.start_conversion, FIF.PLAY, True),
                ("pause", "暂停", self.pause_conversion, FIF.PAUSE, False),
                ("resume", "继续", self.resume_conversion, FIF.PLAY, False),
                ("stop", "停止", self.stop_conversion, toolbar_icon("stop"), False),
            ],
            [
                ("retry", "重试失败", self.retry_failed_tasks, FIF.SYNC, False),
                ("output", "输出目录", self.open_output_dir, FIF.FOLDER, False),
            ],
            [
                ("settings", "设置", self.open_settings, FIF.SETTING, False),
                ("history", "历史任务", self.load_recent_tasks, FIF.HISTORY, False),
                ("clear", "清理任务", self.clear_tasks, FIF.DELETE, False),
            ],
        ]
        for group_index, group in enumerate(groups):
            if group_index:
                self._add_toolbar_gap(toolbar)
            for key, text, slot, icon_key, is_primary in group:
                button = PrimaryPushButton() if is_primary else PushButton()
                button.setText(text)
                button.setIcon(icon_key)
                button.setIconSize(QSize(18, 18))
                button.setFixedHeight(38)
                button.clicked.connect(slot)
                toolbar.addWidget(button)
                self.toolbar_buttons[key] = button
        self.update_toolbar_state()

    def _add_toolbar_gap(self, toolbar: QToolBar) -> None:
        spacer = QWidget(toolbar)
        spacer.setFixedWidth(14)
        action = QWidgetAction(toolbar)
        action.setDefaultWidget(spacer)
        toolbar.addAction(action)

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
        self.conversion_paused = False
        self.update_toolbar_state()

    def pause_conversion(self) -> None:
        if self.worker:
            self.worker.pause()
            self.conversion_paused = True
            self.update_toolbar_state()

    def resume_conversion(self) -> None:
        if self.worker:
            self.worker.resume()
            self.conversion_paused = False
            self.update_toolbar_state()

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
        self.conversion_paused = False
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
        target_ids = self.task_table.checked_task_ids()
        if target_ids:
            targets = [task for task in self.tasks if task.id in target_ids]
        else:
            task = self.current_task()
            targets = [task] if task is not None else []
        if not targets:
            return
        for task in targets:
            for key, value in values.items():
                setattr(task, key, value)
            task.log("已更新书籍元数据")
            self.manager.repository.save_task(task)
            row = self._row_for_task(task.id)
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
        self.update_toolbar_state()

    def update_toolbar_state(self) -> None:
        if not self.toolbar_buttons:
            return
        has_tasks = bool(self.tasks)
        is_running = self.worker is not None
        has_failed = any(task.status == "失败" for task in self.tasks)
        has_pending = any(task.status in {"等待中", "失败", "已取消"} for task in self.tasks)

        states = {
            "import": True,
            "import_folder": True,
            "output": True,
            "settings": True,
            "history": True,
            "start": has_pending and not is_running,
            "pause": is_running and not self.conversion_paused,
            "resume": is_running and self.conversion_paused,
            "stop": is_running,
            "retry": has_failed and not is_running,
            "clear": has_tasks and not is_running,
        }
        for key, enabled in states.items():
            self.toolbar_buttons[key].setEnabled(enabled)

    def load_recent_tasks(self, checked: bool = False, show_empty: bool = True) -> None:
        existing_ids = {task.id for task in self.tasks}
        added = 0
        for task in self.manager.repository.list_recent_tasks(50):
            if task.id in existing_ids:
                continue
            if not task.source_path.exists():
                task.error_message = "源文件不存在"
            self.tasks.append(task)
            self.task_table.add_task(task)
            existing_ids.add(task.id)
            added += 1
        self.update_summary()
        if self.tasks and self.task_table.selected_row() < 0:
            self.task_table.selectRow(0)
        if added == 0 and show_empty:
            QMessageBox.information(self, "没有历史任务", "当前没有可恢复的历史任务。")

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
        self.setObjectName("settingsDialog")
        self.output_dir_edit = FluentLineEdit()
        self.output_dir_edit.setText(config.output_dir)
        self.overwrite_check = CheckBox()
        self.overwrite_check.setChecked(config.overwrite_existing)
        self.keep_structure_check = CheckBox()
        self.keep_structure_check.setChecked(config.keep_folder_structure)
        self.language_edit = FluentLineEdit()
        self.language_edit.setText(config.default_language)
        self.author_edit = FluentLineEdit()
        self.author_edit.setText(config.default_author)
        self.concurrency_spin = SpinBox()
        self.concurrency_spin.setRange(1, 16)
        self.concurrency_spin.setValue(config.max_concurrency)
        self.calibre_edit = FluentLineEdit()
        self.calibre_edit.setText(config.calibre_path)
        self.epubcheck_edit = FluentLineEdit()
        self.epubcheck_edit.setText(config.epubcheck_path)
        self.preset_combo = FluentComboBox()
        self.preset_combo.addItems(conversion_preset_names())
        self.preset_combo.setCurrentText(config.conversion_preset)
        self.preset_combo.currentTextChanged.connect(self.apply_conversion_preset)
        self.chapter_rule_combo = FluentComboBox()
        self.chapter_rule_combo.addItems(["default", "custom", "fixed_size", "blank_lines", "none"])
        self.chapter_rule_combo.setCurrentText(config.chapter_rule)
        self.custom_regex_edit = FluentTextEdit()
        self.custom_regex_edit.setPlainText(config.custom_chapter_regex)
        self.custom_regex_edit.setFixedHeight(82)
        self.fixed_chars_spin = SpinBox()
        self.fixed_chars_spin.setRange(1000, 100000)
        self.fixed_chars_spin.setSingleStep(500)
        self.fixed_chars_spin.setValue(config.fixed_chapter_chars)
        self.css_template_combo = FluentComboBox()
        self.css_template_combo.addItems(css_template_names())
        self.css_template_combo.setCurrentText(config.css_template)
        self.css_template_combo.currentTextChanged.connect(self.apply_css_template)
        self.default_css_edit = FluentTextEdit()
        self.default_css_edit.setPlainText(config.default_css)
        self.default_css_edit.setFixedHeight(120)

        browse_output = PushButton()
        browse_output.setText("选择")
        browse_output.setIcon(FIF.FOLDER)
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
        form.addRow("EPUBCheck 路径", self.epubcheck_edit)
        form.addRow("转换预设", self.preset_combo)
        form.addRow("章节规则", self.chapter_rule_combo)
        form.addRow("自定义章节正则", self.custom_regex_edit)
        form.addRow("固定字数分章", self.fixed_chars_spin)
        form.addRow("CSS 模板", self.css_template_combo)
        form.addRow("默认 CSS 样式", self.default_css_edit)

        ok_button = PrimaryPushButton()
        ok_button.setText("保存")
        ok_button.setIcon(FIF.SAVE)
        cancel_button = PushButton()
        cancel_button.setText("取消")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def apply_conversion_preset(self, name: str) -> None:
        preset = CONVERSION_PRESETS.get(name)
        if preset is None:
            return
        self.chapter_rule_combo.setCurrentText(preset.chapter_rule)
        self.custom_regex_edit.setPlainText(preset.custom_chapter_regex)
        self.fixed_chars_spin.setValue(preset.fixed_chapter_chars)
        self.css_template_combo.setCurrentText(preset.css_template)
        self.apply_css_template(preset.css_template)

    def apply_css_template(self, name: str) -> None:
        template = CSS_TEMPLATES.get(name)
        if template is not None:
            self.default_css_edit.setPlainText(template.css)

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
            epubcheck_path=self.epubcheck_edit.text().strip(),
            conversion_preset=self.preset_combo.currentText(),
            css_template=self.css_template_combo.currentText(),
            default_css=self.default_css_edit.toPlainText(),
        )


def run_app() -> int:
    app = QApplication([])
    app.setApplicationName("EpubForge")
    app.setApplicationDisplayName("EpubForge 电子书工坊")
    app.setOrganizationName("Bixers")
    app.setFont(QFont("Microsoft YaHei UI", 9))
    icon_path = app_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    setTheme(Theme.LIGHT)
    setThemeColor("#1463ff")
    apply_light_palette(app)
    app.setStyleSheet(APP_STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()
