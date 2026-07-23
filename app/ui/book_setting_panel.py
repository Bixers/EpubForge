from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.models import ConvertTask


class BookSettingPanel(QWidget):
    apply_requested = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.title_edit = QLineEdit()
        self.author_edit = QLineEdit()
        self.language_edit = QLineEdit("zh-CN")
        self.publisher_edit = QLineEdit()
        self.keywords_edit = QLineEdit()
        self.cover_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(96)

        cover_button = QPushButton("选择")
        cover_button.clicked.connect(self.choose_cover)
        cover_row = QHBoxLayout()
        cover_row.addWidget(self.cover_edit)
        cover_row.addWidget(cover_button)

        form = QFormLayout()
        form.addRow("书名", self.title_edit)
        form.addRow("作者", self.author_edit)
        form.addRow("语言", self.language_edit)
        form.addRow("出版社", self.publisher_edit)
        form.addRow("关键词", self.keywords_edit)
        form.addRow("封面", cover_row)
        form.addRow("简介", self.description_edit)

        self.apply_button = QPushButton("应用到选中任务")
        self.apply_button.clicked.connect(self.emit_apply)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.apply_button)
        layout.addStretch(1)
        self.setEnabled(False)

    def set_task(self, task: ConvertTask | None) -> None:
        self.setEnabled(task is not None)
        if task is None:
            self.title_edit.clear()
            self.author_edit.clear()
            self.language_edit.setText("zh-CN")
            self.publisher_edit.clear()
            self.keywords_edit.clear()
            self.cover_edit.clear()
            self.description_edit.clear()
            return
        self.title_edit.setText(task.display_title)
        self.author_edit.setText(task.author)
        self.language_edit.setText(task.language)
        self.publisher_edit.setText(task.publisher)
        self.keywords_edit.setText(task.keywords)
        self.cover_edit.setText(task.cover_path)
        self.description_edit.setPlainText(task.description)

    def emit_apply(self) -> None:
        self.apply_requested.emit(
            {
                "title": self.title_edit.text().strip(),
                "author": self.author_edit.text().strip(),
                "language": self.language_edit.text().strip() or "zh-CN",
                "publisher": self.publisher_edit.text().strip(),
                "keywords": self.keywords_edit.text().strip(),
                "cover_path": self.cover_edit.text().strip(),
                "description": self.description_edit.toPlainText().strip(),
            }
        )

    def choose_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择封面图片",
            str(Path.home()),
            "Images (*.jpg *.jpeg *.png *.gif *.webp)",
        )
        if path:
            self.cover_edit.setText(path)

