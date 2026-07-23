from __future__ import annotations

from PySide6.QtWidgets import QListWidget, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.core.models import AppConfig, ConvertTask
from app.core.parser.txt_parser import TxtParser


class ChapterPreviewPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.task: ConvertTask | None = None
        self.config: AppConfig | None = None
        self.chapters = []

        self.refresh_button = QPushButton("刷新预览")
        self.refresh_button.clicked.connect(self.refresh_preview)
        self.chapter_list = QListWidget()
        self.chapter_list.currentRowChanged.connect(self.show_chapter)
        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.chapter_list, 2)
        layout.addWidget(self.content_view, 3)
        self.setEnabled(False)

    def set_task(self, task: ConvertTask | None, config: AppConfig) -> None:
        self.task = task
        self.config = config
        self.setEnabled(task is not None and task.source_format == "txt")
        self.chapter_list.clear()
        self.content_view.clear()
        self.chapters = []
        if self.isEnabled():
            self.refresh_preview()

    def refresh_preview(self) -> None:
        if self.task is None or self.config is None:
            return
        try:
            document = TxtParser(
                self.config.chapter_rule,
                self.config.custom_chapter_regex,
                self.config.fixed_chapter_chars,
            ).parse(
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
        self.chapter_list.clear()
        for chapter in self.chapters:
            self.chapter_list.addItem(f"{chapter.index:03d} {chapter.title}")
        if self.chapters:
            self.chapter_list.setCurrentRow(0)

    def show_chapter(self, row: int) -> None:
        if row < 0 or row >= len(self.chapters):
            self.content_view.clear()
            return
        chapter = self.chapters[row]
        self.content_view.setPlainText(chapter.content[:10000])
