from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
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
        self.task: ConvertTask | None = None
        self.title_edit = LineEdit()
        self.author_edit = LineEdit()
        self.language_edit = ComboBox()
        self.language_edit.addItems(["zh-CN", "en", "ja", "ko", "fr", "de", "es"])
        self.publisher_edit = LineEdit()
        self.keywords_edit = LineEdit()
        self.cover_edit = LineEdit()
        self.cover_edit.hide()
        self.description_edit = TextEdit()
        self.description_edit.setMinimumHeight(120)
        self.description_edit.textChanged.connect(self.update_count)
        self.count_label = QLabel("0/1000")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(96, 128)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setText("封面")
        self.cover_preview.setObjectName("coverPreview")
        self.cover_name_label = QLabel("未选择封面")
        self.cover_name_label.setObjectName("coverFileName")
        self.cover_path_label = QLabel("支持 JPG/PNG/WEBP，建议尺寸 1200x1600 像素")
        self.cover_path_label.setObjectName("coverPathHint")
        self.cover_path_label.setWordWrap(True)
        self.cover_info = QLabel("")
        self.cover_info.setObjectName("coverPathHint")
        self.cover_info.setWordWrap(True)

        cover_button = PushButton()
        cover_button.setText("选择封面")
        cover_button.setIcon(FIF.FOLDER)
        cover_button.clicked.connect(self.choose_cover)
        clear_cover_button = PushButton()
        clear_cover_button.setText("清除")
        clear_cover_button.setIcon(FIF.DELETE)
        clear_cover_button.clicked.connect(self.clear_cover)
        generate_cover_button = PushButton()
        generate_cover_button.setText("生成封面")
        generate_cover_button.setIcon(FIF.PHOTO)
        generate_cover_button.clicked.connect(self.generate_cover)
        cover_actions = QHBoxLayout()
        cover_actions.setSpacing(8)
        cover_actions.addWidget(cover_button)
        cover_actions.addWidget(clear_cover_button)
        cover_actions.addWidget(generate_cover_button)
        cover_actions.addStretch(1)

        cover_meta = QVBoxLayout()
        cover_meta.setSpacing(8)
        cover_meta.addWidget(self.cover_name_label)
        cover_meta.addWidget(self.cover_path_label)
        cover_meta.addLayout(cover_actions)
        cover_meta.addWidget(self.cover_info)
        cover_meta.addStretch(1)

        cover_row = QHBoxLayout()
        cover_row.setSpacing(14)
        cover_row.addWidget(self.cover_preview)
        cover_row.addLayout(cover_meta, 1)

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
        form.addRow("简介", self.description_edit)
        form.addRow("", self.count_label)

        self.apply_button = PrimaryPushButton()
        self.apply_button.setText("应用到勾选任务")
        self.apply_button.setIcon(FIF.ACCEPT)
        self.apply_button.clicked.connect(self.emit_apply)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.apply_button)
        layout.addStretch(1)
        self.apply_button.setEnabled(False)

    def set_task(self, task: ConvertTask | None) -> None:
        self.task = task
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

    def clear_cover(self) -> None:
        self.cover_edit.clear()
        self.set_cover_preview("")

    def generate_cover(self) -> str:
        if self.task is None:
            return ""
        title = self.title_edit.text().strip() or self.task.display_title
        author = self.author_edit.text().strip() or self.task.author
        output_dir = self.task.output_path.parent / "covers"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.task.id}_cover.png"

        image = QImage(1200, 1600, QImage.Format.Format_RGB32)
        image.fill(QColor("#f8fafc"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(QRect(0, 0, 1200, 1600), QColor("#f8fafc"))
        painter.fillRect(QRect(70, 70, 1060, 1460), QColor("#ffffff"))
        painter.setPen(QColor("#d5dde8"))
        painter.drawRect(QRect(70, 70, 1060, 1460))

        painter.setPen(QColor("#111827"))
        title_font = QFont("Microsoft YaHei UI", 58)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(
            QRect(150, 420, 900, 420),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            title,
        )

        painter.setPen(QColor("#475569"))
        author_font = QFont("Microsoft YaHei UI", 28)
        painter.setFont(author_font)
        painter.drawText(
            QRect(150, 920, 900, 90),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            author or "EpubForge",
        )

        painter.setPen(QColor("#1463ff"))
        brand_font = QFont("Microsoft YaHei UI", 20)
        painter.setFont(brand_font)
        painter.drawText(QRect(150, 1380, 900, 60), Qt.AlignmentFlag.AlignCenter, "EpubForge")
        painter.end()
        image.save(str(output_path), "PNG")

        self.cover_edit.setText(str(output_path))
        self.set_cover_preview(str(output_path))
        self.emit_apply()
        return str(output_path)

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
                self.cover_name_label.setText(Path(path).name)
                self.cover_name_label.setToolTip(path)
                self.cover_path_label.setText("已选择封面")
                self.cover_path_label.setToolTip(path)
                self.cover_info.setText(f"完整路径：{path}\n文件大小：{size:.2f} MB")
                self.cover_info.setToolTip(path)
                return
        self.cover_preview.setPixmap(QPixmap())
        self.cover_preview.setText("封面")
        self.cover_name_label.setText("未选择封面")
        self.cover_name_label.setToolTip("")
        self.cover_path_label.setText("支持 JPG/PNG/WEBP，建议尺寸 1200x1600 像素")
        self.cover_path_label.setToolTip("")
        self.cover_info.setText("")
        self.cover_info.setToolTip("")

    def update_count(self) -> None:
        count = len(self.description_edit.toPlainText())
        self.count_label.setText(f"{count}/1000")
