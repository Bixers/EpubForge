from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSplitter,
    QFrame,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton, TextEdit, TreeWidget

from app.core.models import AppConfig, ConvertTask
from app.core.parser.html_parser import HtmlParser
from app.core.parser.markdown_parser import MarkdownParser
from app.core.parser.txt_parser import TxtParser


class ChapterPreviewPanel(QWidget):
    chapters_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.task: ConvertTask | None = None
        self.config: AppConfig | None = None
        self.chapters = []
        self.current_row = -1
        self.chapter_items: dict[int, QTreeWidgetItem] = {}

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
        button_row = QHBoxLayout()
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.reset_button)

        self.chapter_tree = TreeWidget()
        self.chapter_tree.setHeaderLabels(["序号", "章节标题"])
        self.chapter_tree.setRootIsDecorated(True)
        self.chapter_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chapter_tree.setMinimumWidth(180)
        self.chapter_tree.itemSelectionChanged.connect(self.change_selected_chapter)
        self.chapter_tree.header().setStretchLastSection(True)
        self.chapter_tree.setColumnWidth(0, 72)
        self.volume_edit = LineEdit()
        self.title_edit = LineEdit()
        self.content_view = TextEdit()
        self.content_view.setAcceptRichText(False)

        meta_frame = QFrame()
        meta_frame.setObjectName("panelFrame")
        meta_layout = QVBoxLayout(meta_frame)
        meta_layout.addWidget(QLabel("所属分卷"))
        meta_layout.addWidget(self.volume_edit)
        meta_layout.addWidget(QLabel("章节标题"))
        meta_layout.addWidget(self.title_edit)

        content_frame = QFrame()
        content_frame.setObjectName("panelFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.addWidget(QLabel("章节内容"))
        content_layout.addWidget(self.content_view, 1)

        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.addWidget(meta_frame)
        editor_splitter.addWidget(content_frame)
        editor_splitter.setSizes([120, 500])
        editor_splitter.setChildrenCollapsible(False)
        editor_splitter.setMinimumWidth(260)

        body = QSplitter(Qt.Orientation.Horizontal)
        body.addWidget(self.chapter_tree)
        body.addWidget(editor_splitter)
        body.setSizes([220, 540])
        body.setChildrenCollapsible(False)

        layout = QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addWidget(body, 1)
        self.setEnabled(False)

    def set_task(self, task: ConvertTask | None, config: AppConfig) -> None:
        self.task = task
        self.config = config
        self.setEnabled(task is not None and task.source_format in {"txt", "markdown", "html"})
        self.chapter_tree.clear()
        self.chapter_items = {}
        self.volume_edit.clear()
        self.title_edit.clear()
        self.content_view.clear()
        self.chapters = []
        self.current_row = -1
        if self.isEnabled():
            if task and task.edited_chapters:
                self.chapters = [chapter for chapter in task.edited_chapters]
                self.populate_chapter_list()
            else:
                self.refresh_preview()

    def refresh_preview(self) -> None:
        if self.task is None or self.config is None:
            return
        self.save_current_chapter()
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
        self.populate_chapter_list()

    def populate_chapter_list(self) -> None:
        selected_row = self.current_row if self.current_row >= 0 else 0
        self.chapter_tree.blockSignals(True)
        self.chapter_tree.clear()
        self.chapter_items = {}
        volume_items: dict[str, QTreeWidgetItem] = {}
        for row, chapter in enumerate(self.chapters):
            if chapter.volume_title:
                parent = volume_items.get(chapter.volume_title)
                if parent is None:
                    parent = QTreeWidgetItem(["分卷", chapter.volume_title])
                    parent.setToolTip(1, chapter.volume_title)
                    parent.setExpanded(True)
                    self.chapter_tree.addTopLevelItem(parent)
                    volume_items[chapter.volume_title] = parent
                item = QTreeWidgetItem([f"{chapter.index:03d}", chapter.title])
                parent.addChild(item)
            else:
                item = QTreeWidgetItem([f"{chapter.index:03d}", chapter.title])
                self.chapter_tree.addTopLevelItem(item)
            item.setData(0, Qt.ItemDataRole.UserRole, row)
            item.setToolTip(0, f"{chapter.index:03d}")
            item.setToolTip(1, chapter.title)
            self.chapter_items[row] = item
        self.chapter_tree.resizeColumnToContents(0)
        self.chapter_tree.blockSignals(False)
        if self.chapters:
            selected_row = min(selected_row, len(self.chapters) - 1)
            item = self.chapter_items.get(selected_row)
            if item is not None:
                self.chapter_tree.setCurrentItem(item)
            self.show_chapter(selected_row)

    def change_selected_chapter(self) -> None:
        item = self.chapter_tree.currentItem()
        row = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if row is None:
            return
        self.show_chapter(int(row))

    def show_chapter(self, row: int) -> None:
        if self.current_row >= 0:
            self._write_editor_to_chapter(self.current_row)
        self.current_row = row
        if row < 0 or row >= len(self.chapters):
            self.volume_edit.clear()
            self.title_edit.clear()
            self.content_view.clear()
            return
        chapter = self.chapters[row]
        self.volume_edit.setText(chapter.volume_title)
        self.title_edit.setText(chapter.title)
        self.content_view.setPlainText(chapter.content)

    def save_current_chapter(self) -> None:
        if self.task is None or not self.chapters:
            return
        if self.current_row >= 0:
            self._write_editor_to_chapter(self.current_row)
        for index, chapter in enumerate(self.chapters, start=1):
            chapter.index = index
        self.task.edited_chapters = [chapter for chapter in self.chapters]
        self.task.log(f"已保存章节编辑：{len(self.chapters)} 章")
        self.populate_chapter_list()
        self.chapters_changed.emit(self.task)

    def reset_to_source(self) -> None:
        if self.task is None:
            return
        self.task.edited_chapters = []
        self.task.log("已还原为源文件章节解析")
        self.refresh_preview()
        self.chapters_changed.emit(self.task)

    def _write_editor_to_chapter(self, row: int) -> None:
        if row < 0 or row >= len(self.chapters):
            return
        self.chapters[row].volume_title = self.volume_edit.text().strip()
        self.chapters[row].title = self.title_edit.text().strip() or f"第 {row + 1} 章"
        self.chapters[row].content = self.content_view.toPlainText()

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
