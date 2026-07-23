from __future__ import annotations

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import ComboBox, FluentIcon as FIF
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton, TextEdit, TreeWidget

from app.core.models import AppConfig, Chapter, ConvertTask
from app.core.chapter.rules import compile_rule_patterns, is_volume_title
from app.core.parser.html_parser import HtmlParser
from app.core.parser.markdown_parser import MarkdownParser
from app.core.parser.text_decoder import decode_text_file
from app.core.parser.txt_parser import TxtParser


NODE_TYPE_ROLE = Qt.ItemDataRole.UserRole
NODE_VALUE_ROLE = Qt.ItemDataRole.UserRole + 1
INSERT_AFTER = "当前位置之后"
INSERT_BEFORE = "当前位置之前"
INSERT_VOLUME_END = "当前分卷末尾"
INSERT_BOOK_END = "全书末尾"
NO_VOLUME = "无分卷"


class ChapterTreeWidget(TreeWidget):
    structure_dropped = Signal()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().dropEvent(event)
        self.structure_dropped.emit()


class FindReplaceDialog(QDialog):
    def __init__(self, panel: "ChapterPreviewPanel") -> None:
        super().__init__(panel)
        self.panel = panel
        self.setWindowTitle("查找替换")
        self.resize(560, 180)
        self.find_edit = LineEdit()
        self.replace_edit = LineEdit()
        self.scope_combo = ComboBox()
        self.scope_combo.addItems(["全书", "当前章节"])
        self.regex_check = QCheckBox("正则")
        self.result_label = QLabel("")

        find_button = PushButton()
        find_button.setText("查找")
        find_button.setIcon(FIF.SEARCH)
        find_button.clicked.connect(self.find_next)
        replace_button = PrimaryPushButton()
        replace_button.setText("全部替换")
        replace_button.setIcon(FIF.EDIT)
        replace_button.clicked.connect(self.replace_all)

        form = QGridLayout()
        form.addWidget(QLabel("查找"), 0, 0)
        form.addWidget(self.find_edit, 0, 1, 1, 3)
        form.addWidget(QLabel("替换为"), 1, 0)
        form.addWidget(self.replace_edit, 1, 1, 1, 3)
        form.addWidget(QLabel("范围"), 2, 0)
        form.addWidget(self.scope_combo, 2, 1)
        form.addWidget(self.regex_check, 2, 2)
        form.addWidget(find_button, 2, 3)

        buttons = QHBoxLayout()
        buttons.addWidget(self.result_label, 1)
        buttons.addWidget(replace_button)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)

    def find_next(self) -> None:
        row = self.panel.find_text(
            self.find_edit.text(),
            regex=self.regex_check.isChecked(),
            all_chapters=self.scope_combo.currentText() == "全书",
        )
        if row is None:
            self.result_label.setText("未找到")
            return
        self.panel.select_chapter(row)
        self.result_label.setText(f"已定位到第 {row + 1} 章")

    def replace_all(self) -> None:
        count = self.panel.replace_text(
            self.find_edit.text(),
            self.replace_edit.text(),
            regex=self.regex_check.isChecked(),
            all_chapters=self.scope_combo.currentText() == "全书",
        )
        self.result_label.setText(f"已替换 {count} 处")


class RecognitionReportDialog(QDialog):
    def __init__(self, panel: "ChapterPreviewPanel") -> None:
        super().__init__(panel)
        self.panel = panel
        self.setWindowTitle("章节识别调试")
        self.resize(760, 520)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["行号", "类型", "规则", "内容"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.itemDoubleClicked.connect(self.apply_selected_as_chapter)

        chapter_button = PrimaryPushButton()
        chapter_button.setText("设为章节")
        chapter_button.setIcon(FIF.ADD)
        chapter_button.clicked.connect(self.apply_selected_as_chapter)
        volume_button = PushButton()
        volume_button.setText("设为分卷")
        volume_button.setIcon(FIF.FOLDER_ADD)
        volume_button.clicked.connect(self.apply_selected_as_volume)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(chapter_button)
        buttons.addWidget(volume_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table, 1)
        layout.addLayout(buttons)
        self.populate()

    def populate(self) -> None:
        rows = self.panel.build_recognition_report()
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column, key in enumerate(["line", "kind", "rule", "text"]):
                item = QTableWidgetItem(str(row[key]))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, row)
                self.table.setItem(row_index, column, item)

    def selected_report_row(self) -> dict | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        item = self.table.item(indexes[0].row(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def apply_selected_as_chapter(self, *_args) -> None:
        row = self.selected_report_row()
        if row:
            self.panel.insert_chapter_marker(row["text"])

    def apply_selected_as_volume(self) -> None:
        row = self.selected_report_row()
        if row:
            self.panel.insert_volume_marker(row["text"])


class QualityReportDialog(QDialog):
    def __init__(self, panel: "ChapterPreviewPanel") -> None:
        super().__init__(panel)
        self.panel = panel
        self.setWindowTitle("章节质量报告")
        self.resize(720, 500)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["级别", "章节", "问题", "详情"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(self.locate_issue)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        self.populate()

    def populate(self) -> None:
        rows = self.panel.build_quality_report()
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [row["level"], str(row["chapter"]), row["issue"], row["detail"]]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, row)
                self.table.setItem(row_index, column, item)

    def locate_issue(self, *_args) -> None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return
        item = self.table.item(indexes[0].row(), 0)
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if row and row["row"] >= 0:
            self.panel.select_chapter(row["row"])


class ReadingPreviewDialog(QDialog):
    def __init__(self, panel: "ChapterPreviewPanel") -> None:
        super().__init__(panel)
        self.panel = panel
        self.setWindowTitle("阅读预览")
        self.resize(720, 680)
        self.scope_combo = ComboBox()
        self.scope_combo.addItems(["当前章节", "全书"])
        self.width_combo = ComboBox()
        self.width_combo.addItems(["手机宽度", "平板宽度", "桌面宽度"])
        self.width_combo.currentTextChanged.connect(self.refresh_preview)
        self.scope_combo.currentTextChanged.connect(self.refresh_preview)
        self.reader = TextEdit()
        self.reader.setReadOnly(True)
        self.reader.setAcceptRichText(False)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("范围"))
        controls.addWidget(self.scope_combo)
        controls.addWidget(QLabel("宽度"))
        controls.addWidget(self.width_combo)
        controls.addStretch(1)
        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.reader, 1)
        self.refresh_preview()

    def refresh_preview(self) -> None:
        width_map = {"手机宽度": 390, "平板宽度": 620, "桌面宽度": 860}
        self.reader.setFixedWidth(width_map.get(self.width_combo.currentText(), 620))
        self.reader.setPlainText(self.panel.preview_text(self.scope_combo.currentText() == "全书"))


class ChapterPreviewPanel(QWidget):
    chapters_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.task: ConvertTask | None = None
        self.config: AppConfig | None = None
        self.chapters: list[Chapter] = []
        self.volume_order: list[str] = []
        self.current_row = -1
        self.current_volume = ""
        self.current_node_type = ""
        self.chapter_items: dict[int, QTreeWidgetItem] = {}
        self.volume_items: dict[str, QTreeWidgetItem] = {}
        self.volume_positions: dict[str, int] = {}

        self.refresh_button = PushButton()
        self.refresh_button.setText("刷新预览")
        self.refresh_button.setIcon(FIF.SYNC)
        self.refresh_button.clicked.connect(self.refresh_preview)
        self.save_button = PrimaryPushButton()
        self.save_button.setText("保存章节修改")
        self.save_button.setIcon(FIF.SAVE)
        self.save_button.clicked.connect(self.save_current_chapter)
        self.reset_button = PushButton()
        self.reset_button.setText("还原源文件解析")
        self.reset_button.setIcon(FIF.RETURN)
        self.reset_button.clicked.connect(self.reset_to_source)
        self.debug_button = PushButton()
        self.debug_button.setText("识别调试")
        self.debug_button.setIcon(FIF.SEARCH)
        self.debug_button.clicked.connect(self.open_recognition_report)
        self.find_replace_button = PushButton()
        self.find_replace_button.setText("查找替换")
        self.find_replace_button.setIcon(FIF.EDIT)
        self.find_replace_button.clicked.connect(self.open_find_replace)
        self.quality_button = PushButton()
        self.quality_button.setText("质量报告")
        self.quality_button.setIcon(FIF.INFO)
        self.quality_button.clicked.connect(self.open_quality_report)
        self.reader_button = PushButton()
        self.reader_button.setText("阅读预览")
        self.reader_button.setIcon(FIF.VIEW)
        self.reader_button.clicked.connect(self.open_reading_preview)

        first_row = QGridLayout()
        first_row.setHorizontalSpacing(8)
        first_row.setVerticalSpacing(8)
        first_row.addWidget(self.refresh_button, 0, 0)
        first_row.addWidget(self.save_button, 0, 1, 1, 2)
        first_row.addWidget(self.reset_button, 0, 3)
        first_row.addWidget(self.debug_button, 1, 0)
        first_row.addWidget(self.find_replace_button, 1, 1)
        first_row.addWidget(self.quality_button, 1, 2)
        first_row.addWidget(self.reader_button, 1, 3)

        self.insert_combo = ComboBox()
        self.insert_combo.addItems([INSERT_AFTER, INSERT_BEFORE, INSERT_VOLUME_END, INSERT_BOOK_END])
        self.add_volume_button = PushButton()
        self.add_volume_button.setText("新增分卷")
        self.add_volume_button.setIcon(FIF.FOLDER_ADD)
        self.add_volume_button.clicked.connect(self.add_volume)
        self.add_chapter_button = PushButton()
        self.add_chapter_button.setText("新增章节")
        self.add_chapter_button.setIcon(FIF.ADD)
        self.add_chapter_button.clicked.connect(self.add_chapter)
        self.move_up_button = PushButton()
        self.move_up_button.setText("上移")
        self.move_up_button.setIcon(FIF.UP)
        self.move_up_button.clicked.connect(self.move_selected_up)
        self.move_down_button = PushButton()
        self.move_down_button.setText("下移")
        self.move_down_button.setIcon(FIF.DOWN)
        self.move_down_button.clicked.connect(self.move_selected_down)
        self.delete_button = PushButton()
        self.delete_button.setText("删除")
        self.delete_button.setIcon(FIF.DELETE)
        self.delete_button.clicked.connect(self.delete_selected)
        self.target_volume_combo = ComboBox()
        self.move_to_volume_button = PushButton()
        self.move_to_volume_button.setText("移入分卷")
        self.move_to_volume_button.setIcon(FIF.FOLDER)
        self.move_to_volume_button.clicked.connect(self.move_selected_to_volume)
        self.merge_button = PushButton()
        self.merge_button.setText("合并")
        self.merge_button.setIcon(FIF.LINK)
        self.merge_button.clicked.connect(self.merge_selected_chapters)
        self.split_button = PushButton()
        self.split_button.setText("拆分")
        self.split_button.setIcon(FIF.CUT)
        self.split_button.clicked.connect(self.split_current_chapter)
        self.clean_button = PushButton()
        self.clean_button.setText("清理文本")
        self.clean_button.setIcon(FIF.BROOM)
        self.clean_button.clicked.connect(self.clean_selected_chapters)

        for button in [
            self.refresh_button,
            self.save_button,
            self.reset_button,
            self.debug_button,
            self.find_replace_button,
            self.quality_button,
            self.reader_button,
            self.add_volume_button,
            self.add_chapter_button,
            self.move_up_button,
            self.move_down_button,
            self.delete_button,
            self.move_to_volume_button,
            self.merge_button,
            self.split_button,
            self.clean_button,
        ]:
            button.setMinimumWidth(88)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.insert_combo.setMinimumWidth(112)
        self.target_volume_combo.setMinimumWidth(112)
        self.insert_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.target_volume_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        insert_label = QLabel("新增位置")
        insert_label.setWordWrap(True)
        batch_label = QLabel("批量归入")
        batch_label.setWordWrap(True)
        structure_row = QGridLayout()
        structure_row.setHorizontalSpacing(8)
        structure_row.setVerticalSpacing(8)
        structure_row.addWidget(insert_label, 0, 0)
        structure_row.addWidget(self.insert_combo, 0, 1)
        structure_row.addWidget(self.add_volume_button, 0, 2)
        structure_row.addWidget(self.add_chapter_button, 0, 3)
        structure_row.addWidget(self.move_up_button, 1, 0)
        structure_row.addWidget(self.move_down_button, 1, 1)
        structure_row.addWidget(self.delete_button, 1, 2)
        structure_row.addWidget(self.clean_button, 1, 3)
        structure_row.addWidget(batch_label, 2, 0)
        structure_row.addWidget(self.target_volume_combo, 2, 1)
        structure_row.addWidget(self.move_to_volume_button, 2, 2)
        structure_row.addWidget(self.merge_button, 2, 3)
        structure_row.addWidget(self.split_button, 3, 3)
        for column in range(4):
            structure_row.setColumnStretch(column, 1)
            first_row.setColumnStretch(column, 1)

        self.chapter_tree = ChapterTreeWidget()
        self.chapter_tree.setHeaderLabels(["序号", "章节结构"])
        self.chapter_tree.setRootIsDecorated(True)
        self.chapter_tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.chapter_tree.setDragEnabled(True)
        self.chapter_tree.setAcceptDrops(True)
        self.chapter_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.chapter_tree.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.chapter_tree.setDropIndicatorShown(True)
        self.chapter_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chapter_tree.setMinimumWidth(160)
        self.chapter_tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.chapter_tree.itemSelectionChanged.connect(self.change_selected_node)
        self.chapter_tree.structure_dropped.connect(self.sync_from_dragged_tree)
        self.chapter_tree.header().setStretchLastSection(True)
        self.chapter_tree.setColumnWidth(0, 72)
        self.volume_edit = LineEdit()
        self.title_edit = LineEdit()
        self.content_view = TextEdit()
        self.content_view.setAcceptRichText(False)

        meta_frame = QFrame()
        meta_frame.setObjectName("panelFrame")
        meta_layout = QVBoxLayout(meta_frame)
        meta_layout.addWidget(QLabel("所属分卷 / 分卷标题"))
        meta_layout.addWidget(self.volume_edit)
        meta_layout.addWidget(QLabel("章节标题"))
        meta_layout.addWidget(self.title_edit)

        content_frame = QFrame()
        content_frame.setObjectName("panelFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.addWidget(QLabel("章节内容"))
        content_layout.addWidget(self.content_view, 1)

        self.editor_splitter = QSplitter(Qt.Orientation.Vertical)
        self.editor_splitter.setObjectName("editorSplitter")
        self.editor_splitter.addWidget(meta_frame)
        self.editor_splitter.addWidget(content_frame)
        self.editor_splitter.setHandleWidth(10)
        self.editor_splitter.setOpaqueResize(True)
        self.editor_splitter.setSizes([120, 500])
        self.editor_splitter.setChildrenCollapsible(False)
        self.editor_splitter.setMinimumWidth(220)
        self.editor_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.body_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.body_splitter.setObjectName("chapterBodySplitter")
        self.body_splitter.addWidget(self.chapter_tree)
        self.body_splitter.addWidget(self.editor_splitter)
        self.body_splitter.setHandleWidth(10)
        self.body_splitter.setOpaqueResize(True)
        self.body_splitter.setSizes([240, 420])
        self.body_splitter.setStretchFactor(0, 2)
        self.body_splitter.setStretchFactor(1, 3)
        self.body_splitter.setChildrenCollapsible(False)

        layout = QVBoxLayout(self)
        layout.addLayout(first_row)
        layout.addLayout(structure_row)
        layout.addWidget(self.body_splitter, 1)
        self._set_task_controls_enabled(False)

    def _set_task_controls_enabled(self, enabled: bool) -> None:
        for widget in [
            self.refresh_button,
            self.save_button,
            self.reset_button,
            self.debug_button,
            self.find_replace_button,
            self.quality_button,
            self.reader_button,
            self.insert_combo,
            self.add_volume_button,
            self.add_chapter_button,
            self.move_up_button,
            self.move_down_button,
            self.delete_button,
            self.clean_button,
            self.target_volume_combo,
            self.move_to_volume_button,
            self.merge_button,
            self.split_button,
            self.chapter_tree,
        ]:
            widget.setEnabled(enabled)
        self.volume_edit.setEnabled(False)
        self.title_edit.setEnabled(False)
        self.content_view.setEnabled(False)

    def set_task(self, task: ConvertTask | None, config: AppConfig) -> None:
        self.task = task
        self.config = config
        is_supported_task = task is not None and task.source_format in {"txt", "markdown", "html"}
        self._set_task_controls_enabled(is_supported_task)
        self.chapter_tree.clear()
        self.chapter_items = {}
        self.volume_items = {}
        self.volume_positions = {}
        self.volume_edit.clear()
        self.title_edit.clear()
        self.content_view.clear()
        self.chapters = []
        self.volume_order = []
        self.current_row = -1
        self.current_volume = ""
        self.current_node_type = ""
        if is_supported_task:
            if task and task.edited_chapters:
                self.chapters = [chapter for chapter in task.edited_chapters]
                self._sync_volume_order_from_chapters()
                self.populate_chapter_tree()
            else:
                self.refresh_preview()

    def refresh_preview(self) -> None:
        if self.task is None or self.config is None:
            return
        self._write_editor_to_current_node()
        try:
            parser = self._parser_for(self.task.source_format)
            document = parser.parse(
                self.task.source_path,
                title=self.task.display_title,
                author=self.task.author,
                language=self.task.language,
                publisher=self.task.publisher,
                description=self.task.description,
                keywords=self.task.keywords,
                cover_path=self.task.cover_path,
            )
        except Exception as exc:
            self.content_view.setPlainText(f"预览失败：{exc}")
            return
        self.chapters = document.chapters
        self.task.edited_chapters = []
        self._sync_volume_order_from_chapters()
        self.populate_chapter_tree()

    def populate_chapter_tree(self, selected: tuple[str, int | str] | None = None) -> None:
        if selected is None:
            selected = self._current_selection_key()
        if selected is None and self.chapters:
            selected = ("chapter", min(max(self.current_row, 0), len(self.chapters) - 1))

        self.chapter_tree.blockSignals(True)
        self.chapter_tree.clear()
        self.chapter_items = {}
        self.volume_items = {}

        self._sync_volume_order_from_chapters()
        volume_children: dict[str, list[tuple[int, Chapter]]] = {volume: [] for volume in self.volume_order}
        for row, chapter in enumerate(self.chapters):
            volume = chapter.volume_title.strip()
            if volume:
                volume_children.setdefault(volume, []).append((row, chapter))
                if volume not in self.volume_order:
                    self.volume_order.append(volume)

        rendered_volumes: set[str] = set()
        empty_volumes = [volume for volume in self.volume_order if not volume_children.get(volume)]
        for volume in empty_volumes:
            self.volume_positions.setdefault(volume, len(self.chapters))

        for row, chapter in enumerate(self.chapters):
            self._add_empty_volumes_at(row, empty_volumes, rendered_volumes)
            volume = chapter.volume_title.strip()
            if not volume:
                self._add_chapter_item(row, chapter, None)
            elif volume not in rendered_volumes:
                self._add_volume_item(volume, volume_children.get(volume, []))
                rendered_volumes.add(volume)
        self._add_empty_volumes_at(len(self.chapters), empty_volumes, rendered_volumes, include_after=True)

        self.chapter_tree.resizeColumnToContents(0)
        self.chapter_tree.blockSignals(False)
        self._refresh_target_volume_combo()
        self._restore_selection(selected)
        self._update_editor_enabled()

    def _add_volume_item(self, volume: str, children: list[tuple[int, Chapter]]) -> QTreeWidgetItem:
        parent = QTreeWidgetItem(["分卷", volume])
        parent.setData(0, NODE_TYPE_ROLE, "volume")
        parent.setData(0, NODE_VALUE_ROLE, volume)
        parent.setToolTip(1, volume)
        parent.setExpanded(True)
        self.chapter_tree.addTopLevelItem(parent)
        self.volume_items[volume] = parent
        for row, chapter in children:
            self._add_chapter_item(row, chapter, parent)
        return parent

    def _add_empty_volumes_at(
        self,
        row: int,
        empty_volumes: list[str],
        rendered_volumes: set[str],
        include_after: bool = False,
    ) -> None:
        for volume in empty_volumes:
            if volume in rendered_volumes:
                continue
            position = self.volume_positions.get(volume, len(self.chapters))
            if position == row or (include_after and position >= row):
                self._add_volume_item(volume, [])
                rendered_volumes.add(volume)

    def _add_chapter_item(
        self,
        row: int,
        chapter: Chapter,
        parent: QTreeWidgetItem | None,
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem([f"{chapter.index:03d}", chapter.title])
        item.setData(0, NODE_TYPE_ROLE, "chapter")
        item.setData(0, NODE_VALUE_ROLE, row)
        item.setToolTip(0, f"{chapter.index:03d}")
        item.setToolTip(1, chapter.title)
        if parent is None:
            self.chapter_tree.addTopLevelItem(item)
        else:
            parent.addChild(item)
        self.chapter_items[row] = item
        return item

    def change_selected_node(self) -> None:
        self._write_editor_to_current_node()
        item = self.chapter_tree.currentItem()
        if item is None:
            self.current_node_type = ""
            self.current_row = -1
            self.current_volume = ""
            self.volume_edit.clear()
            self.title_edit.clear()
            self.content_view.clear()
            self._update_editor_enabled()
            return

        node_type = item.data(0, NODE_TYPE_ROLE)
        value = item.data(0, NODE_VALUE_ROLE)
        if node_type == "volume":
            self.current_node_type = "volume"
            self.current_row = -1
            self.current_volume = str(value)
            self.volume_edit.setText(self.current_volume)
            self.title_edit.clear()
            self.content_view.clear()
        elif node_type == "chapter":
            self.show_chapter(int(value))
        self._update_editor_enabled()

    def show_chapter(self, row: int) -> None:
        self.current_node_type = "chapter"
        self.current_row = row
        self.current_volume = ""
        if row < 0 or row >= len(self.chapters):
            self.volume_edit.clear()
            self.title_edit.clear()
            self.content_view.clear()
            return
        chapter = self.chapters[row]
        self.volume_edit.setText(chapter.volume_title)
        self.title_edit.setText(chapter.title)
        self.content_view.setPlainText(chapter.content)

    def add_volume(self) -> None:
        self._write_editor_to_current_node()
        title = self._unique_volume_title("新建分卷")
        position = self._volume_insert_position()
        index = self._volume_insert_index(position)
        self.volume_order.insert(index, title)
        self.volume_positions[title] = position
        self.current_node_type = "volume"
        self.current_volume = title
        self.current_row = -1
        self.populate_chapter_tree(("volume", title))
        self._mark_changed("已新增分卷")

    def add_chapter(self) -> None:
        self._write_editor_to_current_node()
        volume = self._target_volume_for_new_chapter()
        chapter = Chapter(0, "新建章节", "", volume_title=volume)
        index = self._chapter_insert_index(volume)
        if volume and volume not in self.volume_order:
            self.volume_order.append(volume)
            self.volume_positions.setdefault(volume, index)
        self.chapters.insert(index, chapter)
        self._renumber_chapters()
        self.current_node_type = "chapter"
        self.current_row = index
        self.current_volume = ""
        self.populate_chapter_tree(("chapter", index))
        self._mark_changed("已新增章节")

    def move_selected_up(self) -> None:
        self._write_editor_to_current_node()
        if self.current_node_type == "chapter" and self.current_row > 0:
            row = self.current_row
            self.chapters[row - 1], self.chapters[row] = self.chapters[row], self.chapters[row - 1]
            self._renumber_chapters()
            self.current_row = row - 1
            self.populate_chapter_tree(("chapter", self.current_row))
            self._mark_changed("已上移章节")
        elif self.current_node_type == "volume" and self.current_volume in self.volume_order:
            index = self.volume_order.index(self.current_volume)
            if index <= 0:
                return
            self.volume_order[index - 1], self.volume_order[index] = self.volume_order[index], self.volume_order[index - 1]
            self._reorder_chapters_by_volume_order()
            self.populate_chapter_tree(("volume", self.current_volume))
            self._mark_changed("已上移分卷")

    def move_selected_down(self) -> None:
        self._write_editor_to_current_node()
        if self.current_node_type == "chapter" and 0 <= self.current_row < len(self.chapters) - 1:
            row = self.current_row
            self.chapters[row + 1], self.chapters[row] = self.chapters[row], self.chapters[row + 1]
            self._renumber_chapters()
            self.current_row = row + 1
            self.populate_chapter_tree(("chapter", self.current_row))
            self._mark_changed("已下移章节")
        elif self.current_node_type == "volume" and self.current_volume in self.volume_order:
            index = self.volume_order.index(self.current_volume)
            if index >= len(self.volume_order) - 1:
                return
            self.volume_order[index + 1], self.volume_order[index] = self.volume_order[index], self.volume_order[index + 1]
            self._reorder_chapters_by_volume_order()
            self.populate_chapter_tree(("volume", self.current_volume))
            self._mark_changed("已下移分卷")

    def delete_selected(self) -> None:
        self._write_editor_to_current_node()
        if self.current_node_type == "chapter" and 0 <= self.current_row < len(self.chapters):
            removed_index = self.current_row
            self.chapters.pop(removed_index)
            self._renumber_chapters()
            if self.chapters:
                self.current_row = min(removed_index, len(self.chapters) - 1)
                selected: tuple[str, int | str] | None = ("chapter", self.current_row)
            else:
                self.current_row = -1
                selected = None
            self.populate_chapter_tree(selected)
            self._mark_changed("已删除章节")
        elif self.current_node_type == "volume" and self.current_volume:
            volume = self.current_volume
            self.chapters = [chapter for chapter in self.chapters if chapter.volume_title != volume]
            self.volume_order = [item for item in self.volume_order if item != volume]
            self.volume_positions.pop(volume, None)
            self._renumber_chapters()
            self.current_volume = ""
            self.current_node_type = ""
            self.current_row = -1
            self.populate_chapter_tree()
            self._mark_changed("已删除分卷")

    def save_current_chapter(self) -> None:
        self._write_editor_to_current_node()
        self._renumber_chapters()
        if self.task is None:
            return
        self.task.edited_chapters = [chapter for chapter in self.chapters]
        self.task.log(f"已保存章节编辑：{len(self.chapters)} 章")
        self.populate_chapter_tree()
        self.chapters_changed.emit(self.task)

    def reset_to_source(self) -> None:
        if self.task is None:
            return
        self.task.edited_chapters = []
        self.task.log("已还原为源文件章节解析")
        self.refresh_preview()
        self.chapters_changed.emit(self.task)

    def open_find_replace(self) -> None:
        FindReplaceDialog(self).exec()

    def open_recognition_report(self) -> None:
        RecognitionReportDialog(self).exec()

    def open_quality_report(self) -> None:
        QualityReportDialog(self).exec()

    def open_reading_preview(self) -> None:
        ReadingPreviewDialog(self).exec()

    def find_text(self, pattern: str, regex: bool = False, all_chapters: bool = True) -> int | None:
        self._write_editor_to_current_node()
        if not pattern:
            return None
        rows = range(len(self.chapters)) if all_chapters else [self.current_row]
        for row in rows:
            if row < 0 or row >= len(self.chapters):
                continue
            if self._contains_text(self.chapters[row].title, pattern, regex) or self._contains_text(
                self.chapters[row].content, pattern, regex
            ):
                return row
        return None

    def replace_text(self, pattern: str, replacement: str, regex: bool = False, all_chapters: bool = True) -> int:
        self._write_editor_to_current_node()
        if not pattern:
            return 0
        rows = list(range(len(self.chapters))) if all_chapters else [self.current_row]
        total = 0
        for row in rows:
            if row < 0 or row >= len(self.chapters):
                continue
            chapter = self.chapters[row]
            chapter.title, title_count = self._replace_text_value(chapter.title, pattern, replacement, regex)
            chapter.content, content_count = self._replace_text_value(chapter.content, pattern, replacement, regex)
            total += title_count + content_count
        if total:
            self.populate_chapter_tree(self._current_selection_key())
            self._mark_changed(f"已替换 {total} 处文本")
        return total

    def build_quality_report(self) -> list[dict]:
        self._write_editor_to_current_node()
        report: list[dict] = []
        if not self.chapters:
            return [{"row": -1, "level": "错误", "chapter": "-", "issue": "无章节", "detail": "当前任务没有可输出章节"}]
        title_seen: dict[str, int] = {}
        for row, chapter in enumerate(self.chapters):
            title = chapter.title.strip()
            display_title = title or f"第 {row + 1} 章"
            length = len(chapter.content.strip())
            if not title:
                report.append(self._quality_item(row, "错误", display_title, "缺少标题", "章节标题为空"))
            title_seen[title] = title_seen.get(title, 0) + 1
            if title and title_seen[title] > 1:
                report.append(self._quality_item(row, "警告", display_title, "重复标题", title))
            if not chapter.content.strip():
                report.append(self._quality_item(row, "错误", display_title, "空章节", "章节内容为空"))
            elif length < 20:
                report.append(self._quality_item(row, "提示", display_title, "内容过短", f"{length} 字"))
            elif length > 30000:
                report.append(self._quality_item(row, "警告", display_title, "内容过长", f"{length} 字，建议拆分"))
            if "\ufffd" in chapter.content:
                report.append(self._quality_item(row, "警告", display_title, "疑似乱码", "内容包含替换字符 �"))
            if re.search(r"https?://|www\.", chapter.content, re.IGNORECASE):
                report.append(self._quality_item(row, "提示", display_title, "疑似广告链接", "内容包含网址"))
        volumes = {chapter.volume_title.strip() for chapter in self.chapters if chapter.volume_title.strip()}
        if not volumes:
            report.append(self._quality_item(-1, "提示", "-", "无分卷", "全书章节均未设置分卷"))
        return report

    def build_recognition_report(self) -> list[dict]:
        lines = self._source_lines()
        patterns = self._recognition_patterns()
        report: list[dict] = []
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            matched = next((pattern for pattern in patterns if pattern.match(stripped)), None)
            if matched:
                kind = "分卷" if is_volume_title(stripped) else "章节"
                report.append({"line": line_number, "kind": kind, "rule": matched.pattern, "text": stripped})
            elif self._looks_like_heading(stripped):
                report.append({"line": line_number, "kind": "疑似标题", "rule": "heuristic", "text": stripped})
        return report

    def insert_chapter_marker(self, title: str) -> None:
        title = title.strip()
        if not title:
            return
        self._write_editor_to_current_node()
        if 0 <= self.current_row < len(self.chapters):
            self.chapters.insert(self.current_row + 1, Chapter(0, title, "", volume_title=self.chapters[self.current_row].volume_title))
            selected = ("chapter", self.current_row + 1)
        else:
            self.chapters.append(Chapter(0, title, ""))
            selected = ("chapter", len(self.chapters) - 1)
        self._renumber_chapters()
        self.populate_chapter_tree(selected)
        self._mark_changed("已从识别调试新增章节")

    def insert_volume_marker(self, title: str) -> None:
        title = title.strip()
        if not title:
            return
        self._write_editor_to_current_node()
        title = self._unique_volume_title(title)
        position = self.current_row if self.current_row >= 0 else len(self.chapters)
        self.volume_order.insert(self._volume_insert_index(position), title)
        self.volume_positions[title] = position
        self.populate_chapter_tree(("volume", title))
        self._mark_changed("已从识别调试新增分卷")

    def select_chapter(self, row: int) -> None:
        if row < 0 or row >= len(self.chapters):
            return
        item = self.chapter_items.get(row)
        if item is not None:
            self.chapter_tree.setCurrentItem(item)
            self.chapter_tree.scrollToItem(item)
        else:
            self.show_chapter(row)

    def preview_text(self, all_chapters: bool = False) -> str:
        self._write_editor_to_current_node()
        if all_chapters:
            chapters = self.chapters
        elif 0 <= self.current_row < len(self.chapters):
            chapters = [self.chapters[self.current_row]]
        else:
            chapters = self.chapters[:1]
        blocks: list[str] = []
        current_volume = ""
        for chapter in chapters:
            volume = chapter.volume_title.strip()
            if volume and volume != current_volume:
                blocks.append(f"【{volume}】")
                current_volume = volume
            blocks.append(chapter.title.strip() or f"第 {chapter.index} 章")
            blocks.append(chapter.content.strip())
        return "\n\n".join(block for block in blocks if block)

    def _quality_item(self, row: int, level: str, chapter: str, issue: str, detail: str) -> dict:
        return {"row": row, "level": level, "chapter": chapter, "issue": issue, "detail": detail}

    def _contains_text(self, text: str, pattern: str, regex: bool) -> bool:
        if regex:
            try:
                return re.search(pattern, text) is not None
            except re.error:
                return False
        return pattern in text

    def _replace_text_value(self, text: str, pattern: str, replacement: str, regex: bool) -> tuple[str, int]:
        if regex:
            try:
                return re.subn(pattern, replacement, text)
            except re.error:
                return text, 0
        return text.replace(pattern, replacement), text.count(pattern)

    def _source_lines(self) -> list[str]:
        if self.task is None or not self.task.source_path.exists():
            return []
        try:
            text, _encoding = decode_text_file(self.task.source_path)
        except OSError:
            return []
        if self.task.source_format == "txt":
            text = TxtParser()._clean_text(text)
        return text.replace("\r\n", "\n").replace("\r", "\n").splitlines()

    def _recognition_patterns(self) -> list[re.Pattern[str]]:
        if self.config and self.config.chapter_rule == "custom":
            patterns = [item.strip() for item in re.split(r"[\r\n;]+", self.config.custom_chapter_regex) if item.strip()]
            compiled: list[re.Pattern[str]] = []
            for pattern in patterns:
                try:
                    compiled.append(re.compile(pattern, re.IGNORECASE))
                except re.error:
                    continue
            return compiled
        custom = self.config.custom_chapter_regex if self.config else ""
        try:
            return compile_rule_patterns(custom)
        except re.error:
            return compile_rule_patterns("")

    def _looks_like_heading(self, text: str) -> bool:
        if len(text) > 80:
            return False
        return bool(re.search(r"(第\s*[\d一二三四五六七八九十百千万零〇两]+\s*[章节卷部回]|卷\s*[\d一二三四五六七八九十]+|部\s*[\d一二三四五六七八九十]+|chapter|part|volume)", text, re.IGNORECASE))

    def _write_editor_to_current_node(self) -> None:
        if self.current_node_type == "chapter" and 0 <= self.current_row < len(self.chapters):
            volume = self.volume_edit.text().strip()
            self.chapters[self.current_row].volume_title = volume
            self.chapters[self.current_row].title = self.title_edit.text().strip() or f"第 {self.current_row + 1} 章"
            self.chapters[self.current_row].content = self.content_view.toPlainText()
            if volume and volume not in self.volume_order:
                self.volume_order.append(volume)
                self.volume_positions.setdefault(volume, self.current_row)
        elif self.current_node_type == "volume" and self.current_volume:
            new_title = self.volume_edit.text().strip() or self.current_volume
            if new_title != self.current_volume:
                self._rename_volume(self.current_volume, new_title)
                self.current_volume = new_title

    def _rename_volume(self, old_title: str, new_title: str) -> None:
        if old_title in self.volume_order:
            self.volume_order[self.volume_order.index(old_title)] = new_title
        elif new_title not in self.volume_order:
            self.volume_order.append(new_title)
        if old_title in self.volume_positions:
            self.volume_positions[new_title] = self.volume_positions.pop(old_title)
        for chapter in self.chapters:
            if chapter.volume_title == old_title:
                chapter.volume_title = new_title

    def _renumber_chapters(self) -> None:
        for index, chapter in enumerate(self.chapters, start=1):
            chapter.index = index

    def _sync_volume_order_from_chapters(self) -> None:
        for chapter in self.chapters:
            volume = chapter.volume_title.strip()
            if volume and volume not in self.volume_order:
                self.volume_order.append(volume)
        self.volume_order = [volume for volume in self.volume_order if volume and any(ch.volume_title == volume for ch in self.chapters) or volume]

    def _reorder_chapters_by_volume_order(self) -> None:
        volume_rank = {volume: index for index, volume in enumerate(self.volume_order)}
        self.chapters.sort(
            key=lambda chapter: (
                0 if not chapter.volume_title else 1,
                volume_rank.get(chapter.volume_title, len(volume_rank)),
                chapter.index,
            )
        )
        self._renumber_chapters()

    def _volume_insert_index(self, position: int | None = None) -> int:
        position = self._volume_insert_position() if position is None else position
        selected_volume = self._selected_volume_title()
        if selected_volume and selected_volume in self.volume_order:
            selected_index = self.volume_order.index(selected_volume)
            return selected_index if self.insert_combo.currentText() == INSERT_BEFORE else selected_index + 1
        for index, volume in enumerate(self.volume_order):
            if self._volume_position(volume) > position:
                return index
        return len(self.volume_order)

    def _volume_insert_position(self) -> int:
        mode = self.insert_combo.currentText()
        if mode == INSERT_BOOK_END:
            return len(self.chapters)
        if self.current_node_type == "chapter" and 0 <= self.current_row < len(self.chapters):
            return self.current_row if mode == INSERT_BEFORE else self.current_row + 1
        selected_volume = self._selected_volume_title()
        if selected_volume:
            indexes = [idx for idx, chapter in enumerate(self.chapters) if chapter.volume_title == selected_volume]
            if indexes:
                if mode == INSERT_BEFORE:
                    return min(indexes)
                return max(indexes) + 1
            return self.volume_positions.get(selected_volume, len(self.chapters))
        return len(self.chapters)

    def _volume_position(self, volume: str) -> int:
        if not volume:
            return len(self.chapters)
        indexes = [idx for idx, chapter in enumerate(self.chapters) if chapter.volume_title == volume]
        if indexes:
            return min(indexes)
        return self.volume_positions.get(volume, len(self.chapters))

    def _chapter_insert_index(self, volume: str) -> int:
        mode = self.insert_combo.currentText()
        if mode == INSERT_BOOK_END:
            return len(self.chapters)
        if mode == INSERT_VOLUME_END and volume:
            indexes = [idx for idx, chapter in enumerate(self.chapters) if chapter.volume_title == volume]
            return (max(indexes) + 1) if indexes else self.volume_positions.get(volume, len(self.chapters))
        if self.current_node_type == "chapter" and 0 <= self.current_row < len(self.chapters):
            return self.current_row if mode == INSERT_BEFORE else self.current_row + 1
        if self.current_node_type == "volume" and volume:
            indexes = [idx for idx, chapter in enumerate(self.chapters) if chapter.volume_title == volume]
            return (max(indexes) + 1) if indexes else self.volume_positions.get(volume, len(self.chapters))
        return len(self.chapters)

    def _target_volume_for_new_chapter(self) -> str:
        if self.current_node_type == "volume":
            return self.current_volume
        if self.current_node_type == "chapter" and 0 <= self.current_row < len(self.chapters):
            return self.chapters[self.current_row].volume_title
        return ""

    def move_selected_to_volume(self) -> None:
        self._write_editor_to_current_node()
        rows = self._selected_chapter_rows()
        if not rows:
            return
        target_volume = self._selected_target_volume()
        if target_volume != NO_VOLUME and target_volume and target_volume not in self.volume_order:
            self.volume_order.append(target_volume)
            self.volume_positions.setdefault(target_volume, min(rows))
        selected_chapters = [self.chapters[row] for row in rows]
        remaining = [chapter for index, chapter in enumerate(self.chapters) if index not in set(rows)]
        for chapter in selected_chapters:
            chapter.volume_title = "" if target_volume == NO_VOLUME else target_volume

        if target_volume == NO_VOLUME:
            insert_at = min(rows)
        else:
            target_indexes = [idx for idx, chapter in enumerate(remaining) if chapter.volume_title == target_volume]
            insert_at = (max(target_indexes) + 1) if target_indexes else self._volume_position(target_volume)
            insert_at = min(max(insert_at, 0), len(remaining))
        self.chapters = remaining[:insert_at] + selected_chapters + remaining[insert_at:]
        self._renumber_chapters()
        selected = ("chapter", insert_at) if selected_chapters else self._current_selection_key()
        self.populate_chapter_tree(selected)
        self._mark_changed(f"已将 {len(selected_chapters)} 章移入分卷")

    def merge_selected_chapters(self) -> None:
        self._write_editor_to_current_node()
        rows = self._selected_chapter_rows()
        if len(rows) < 2:
            return
        first_row = rows[0]
        merged = self.chapters[first_row]
        merged.content = "\n\n".join(self.chapters[row].content.strip() for row in rows if self.chapters[row].content.strip())
        merged.title = merged.title.strip() or f"第 {first_row + 1} 章"
        remove_rows = set(rows[1:])
        self.chapters = [chapter for index, chapter in enumerate(self.chapters) if index not in remove_rows]
        self._renumber_chapters()
        self.current_row = first_row
        self.populate_chapter_tree(("chapter", first_row))
        self._mark_changed(f"已合并 {len(rows)} 章")

    def split_current_chapter(self) -> None:
        self._write_editor_to_current_node()
        row = self.current_row
        if self.current_node_type != "chapter" or row < 0 or row >= len(self.chapters):
            return
        chapter = self.chapters[row]
        content = chapter.content
        if len(content.strip()) < 2:
            return
        cursor_pos = self.content_view.textCursor().position()
        split_at = self._safe_split_position(content, cursor_pos)
        if split_at <= 0 or split_at >= len(content):
            return
        first_content = content[:split_at].strip()
        second_content = content[split_at:].strip()
        if not first_content or not second_content:
            return
        chapter.content = first_content
        new_chapter = Chapter(
            0,
            self._split_title(chapter.title),
            second_content,
            content_format=chapter.content_format,
            volume_title=chapter.volume_title,
        )
        self.chapters.insert(row + 1, new_chapter)
        self._renumber_chapters()
        self.populate_chapter_tree(("chapter", row + 1))
        self._mark_changed("已拆分章节")

    def clean_selected_chapters(self) -> None:
        self._write_editor_to_current_node()
        rows = self._selected_chapter_rows()
        if not rows and 0 <= self.current_row < len(self.chapters):
            rows = [self.current_row]
        if not rows:
            return
        for row in rows:
            self.chapters[row].content = self._clean_text(self.chapters[row].content)
        self.populate_chapter_tree(("chapter", rows[0]))
        self._mark_changed(f"已清理 {len(rows)} 章文本")

    def sync_from_dragged_tree(self) -> None:
        self._write_editor_to_current_node()
        reordered: list[Chapter] = []
        new_volume_order: list[str] = []
        new_positions: dict[str, int] = {}

        for top_index in range(self.chapter_tree.topLevelItemCount()):
            item = self.chapter_tree.topLevelItem(top_index)
            node_type = item.data(0, NODE_TYPE_ROLE)
            if node_type == "volume":
                volume = str(item.data(0, NODE_VALUE_ROLE) or item.text(1)).strip()
                if volume and volume not in new_volume_order:
                    new_volume_order.append(volume)
                    new_positions[volume] = len(reordered)
                for child_index in range(item.childCount()):
                    child = item.child(child_index)
                    if child.data(0, NODE_TYPE_ROLE) != "chapter":
                        continue
                    row = int(child.data(0, NODE_VALUE_ROLE))
                    if 0 <= row < len(self.chapters):
                        chapter = self.chapters[row]
                        chapter.volume_title = volume
                        reordered.append(chapter)
            elif node_type == "chapter":
                row = int(item.data(0, NODE_VALUE_ROLE))
                if 0 <= row < len(self.chapters):
                    chapter = self.chapters[row]
                    chapter.volume_title = ""
                    reordered.append(chapter)

        if len(reordered) != len(self.chapters):
            self.populate_chapter_tree()
            return
        self.chapters = reordered
        self.volume_order = new_volume_order
        self.volume_positions = new_positions
        self._renumber_chapters()
        self.current_row = min(max(self.current_row, 0), len(self.chapters) - 1) if self.chapters else -1
        selected = ("chapter", self.current_row) if self.current_row >= 0 else None
        self.populate_chapter_tree(selected)
        self._mark_changed("已拖拽调整章节结构")

    def _selected_chapter_rows(self) -> list[int]:
        rows: set[int] = set()
        for item in self.chapter_tree.selectedItems():
            node_type = item.data(0, NODE_TYPE_ROLE)
            if node_type == "chapter":
                rows.add(int(item.data(0, NODE_VALUE_ROLE)))
            elif node_type == "volume":
                for child_index in range(item.childCount()):
                    child = item.child(child_index)
                    if child.data(0, NODE_TYPE_ROLE) == "chapter":
                        rows.add(int(child.data(0, NODE_VALUE_ROLE)))
        return sorted(row for row in rows if 0 <= row < len(self.chapters))

    def _safe_split_position(self, content: str, preferred: int) -> int:
        if 0 < preferred < len(content):
            return preferred
        middle = len(content) // 2
        candidates = [match.start() for match in re.finditer(r"\n\s*\n|[。！？!?]\s*", content)]
        if not candidates:
            return middle
        return min(candidates, key=lambda value: abs(value - middle))

    def _split_title(self, title: str) -> str:
        title = title.strip() or "新建章节"
        return title if title.endswith("下") else f"{title} 下"

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\ufeff", "")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        lines = [re.sub(r"[ \t]+$", "", line) for line in text.split("\n")]
        cleaned = "\n".join(lines).strip()
        return re.sub(r"\n{3,}", "\n\n", cleaned)

    def _selected_target_volume(self) -> str:
        value = self.target_volume_combo.currentText().strip()
        return NO_VOLUME if value == NO_VOLUME else value

    def _selected_volume_title(self) -> str:
        if self.current_node_type == "volume":
            return self.current_volume
        if self.current_node_type == "chapter" and 0 <= self.current_row < len(self.chapters):
            return self.chapters[self.current_row].volume_title
        return ""

    def _unique_volume_title(self, base: str) -> str:
        existing = set(self.volume_order)
        if base not in existing:
            return base
        suffix = 2
        while f"{base} {suffix}" in existing:
            suffix += 1
        return f"{base} {suffix}"

    def _refresh_target_volume_combo(self) -> None:
        current = self.target_volume_combo.currentText().strip() or NO_VOLUME
        self.target_volume_combo.blockSignals(True)
        self.target_volume_combo.clear()
        self.target_volume_combo.addItem(NO_VOLUME)
        for volume in self.volume_order:
            if volume:
                self.target_volume_combo.addItem(volume)
        if current in [self.target_volume_combo.itemText(index) for index in range(self.target_volume_combo.count())]:
            self.target_volume_combo.setCurrentText(current)
        else:
            self.target_volume_combo.setCurrentText(NO_VOLUME)
        self.target_volume_combo.blockSignals(False)

    def _restore_selection(self, selected: tuple[str, int | str] | None) -> None:
        item = None
        if selected is not None and selected[0] == "chapter":
            item = self.chapter_items.get(int(selected[1]))
        elif selected is not None and selected[0] == "volume":
            item = self.volume_items.get(str(selected[1]))
        if item is None and self.chapters:
            item = self.chapter_items.get(0)
        if item is not None:
            self.chapter_tree.blockSignals(True)
            self.chapter_tree.setCurrentItem(item)
            self.chapter_tree.blockSignals(False)
            node_type = item.data(0, NODE_TYPE_ROLE)
            value = item.data(0, NODE_VALUE_ROLE)
            if node_type == "volume":
                self.current_node_type = "volume"
                self.current_volume = str(value)
                self.current_row = -1
                self.volume_edit.setText(self.current_volume)
                self.title_edit.clear()
                self.content_view.clear()
            elif node_type == "chapter":
                self.show_chapter(int(value))
        else:
            self.current_node_type = ""
            self.current_row = -1
            self.current_volume = ""
            self.volume_edit.clear()
            self.title_edit.clear()
            self.content_view.clear()

    def _current_selection_key(self) -> tuple[str, int | str] | None:
        if self.current_node_type == "chapter" and self.current_row >= 0:
            return ("chapter", self.current_row)
        if self.current_node_type == "volume" and self.current_volume:
            return ("volume", self.current_volume)
        return None

    def _update_editor_enabled(self) -> None:
        is_chapter = self.current_node_type == "chapter"
        is_volume = self.current_node_type == "volume"
        self.volume_edit.setEnabled(is_chapter or is_volume)
        self.title_edit.setEnabled(is_chapter)
        self.content_view.setEnabled(is_chapter)
        self.move_to_volume_button.setEnabled(bool(self._selected_chapter_rows()))
        selected_count = len(self._selected_chapter_rows())
        self.merge_button.setEnabled(selected_count >= 2)
        self.split_button.setEnabled(is_chapter)
        self.clean_button.setEnabled(is_chapter or selected_count > 0)

    def _mark_changed(self, message: str) -> None:
        self._renumber_chapters()
        if self.task is None:
            return
        self.task.edited_chapters = [chapter for chapter in self.chapters]
        self.task.log(message)
        self.chapters_changed.emit(self.task)

    def _parser_for(self, source_format: str):
        if source_format == "txt":
            return TxtParser(
                self.config.chapter_rule,
                self.config.custom_chapter_regex,
                self.config.fixed_chapter_chars,
            )
        if source_format == "markdown":
            return MarkdownParser()
        return HtmlParser()
