from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import ComboBox, FluentIcon as FIF
from qfluentwidgets import LineEdit, PrimaryPushButton, PushButton, TextEdit

from app.core.models import ConvertTask


class BookSettingPanel(QWidget):
    apply_requested = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.title_edit = LineEdit()
        self.author_edit = LineEdit()
        self.language_edit = ComboBox()
        self.language_edit.addItems(["zh-CN", "en", "ja", "ko", "fr", "de", "es"])
        self.publisher_edit = LineEdit()
        self.keywords_edit = LineEdit()
        self.cover_edit = LineEdit()
        self.description_edit = TextEdit()
        self.description_edit.setMinimumHeight(120)
        self.description_edit.textChanged.connect(self.update_count)
        self.count_label = QLabel("0/1000")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(92, 122)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setText("封面")
        self.cover_preview.setObjectName("coverPreview")
        self.cover_info = QLabel("支持 JPG/PNG/WEBP，建议尺寸 1200x1600 像素")
        self.cover_info.setWordWrap(True)

        cover_button = PushButton()
        cover_button.setText("选择")
        cover_button.setIcon(FIF.FOLDER)
        cover_button.clicked.connect(self.choose_cover)
        cover_row = QHBoxLayout()
        cover_row.addWidget(self.cover_preview)
        cover_row.addWidget(self.cover_edit, 1)
        cover_row.addWidget(cover_button)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        form.addRow("书名", self.title_edit)
        form.addRow("作者", self.author_edit)
        form.addRow("语言", self.language_edit)
        form.addRow("出版社", self.publisher_edit)
        form.addRow("关键词", self.keywords_edit)
        form.addRow("封面", cover_row)
        form.addRow("", self.cover_info)
        form.addRow("简介", self.description_edit)
        form.addRow("", self.count_label)

        self.apply_button = PrimaryPushButton()
        self.apply_button.setText("应用到选中任务")
        self.apply_button.setIcon(FIF.ACCEPT)
        self.apply_button.clicked.connect(self.emit_apply)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.apply_button)
        layout.addStretch(1)
        self.apply_button.setEnabled(False)

    def set_task(self, task: ConvertTask | None) -> None:
        self.apply_button.setEnabled(task is not None)
        if task is None:
            self.title_edit.clear()
            self.author_edit.clear()
            self.language_edit.setCurrentText("zh-CN")
            self.publisher_edit.clear()
            self.keywords_edit.clear()
            self.cover_edit.clear()
            self.set_cover_preview("")
            self.description_edit.clear()
            return
        self.title_edit.setText(task.display_title)
        self.author_edit.setText(task.author)
        self.language_edit.setCurrentText(task.language or "zh-CN")
        self.publisher_edit.setText(task.publisher)
        self.keywords_edit.setText(task.keywords)
        self.cover_edit.setText(task.cover_path)
        self.set_cover_preview(task.cover_path)
        self.description_edit.setPlainText(task.description)
        self.update_count()

    def emit_apply(self) -> None:
        self.apply_requested.emit(
            {
                "title": self.title_edit.text().strip(),
                "author": self.author_edit.text().strip(),
                "language": self.language_edit.currentText().strip() or "zh-CN",
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
            self.set_cover_preview(path)

    def set_cover_preview(self, path: str) -> None:
        if path and Path(path).exists():
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.cover_preview.setPixmap(
                    pixmap.scaled(
                        self.cover_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                size = Path(path).stat().st_size / 1024 / 1024
                self.cover_info.setText(f"支持 JPG/PNG/WEBP | 文件大小：{size:.2f} MB")
                return
        self.cover_preview.setPixmap(QPixmap())
        self.cover_preview.setText("封面")
        self.cover_info.setText("支持 JPG/PNG/WEBP，建议尺寸 1200x1600 像素")

    def update_count(self) -> None:
        count = len(self.description_edit.toPlainText())
        self.count_label.setText(f"{count}/1000")
