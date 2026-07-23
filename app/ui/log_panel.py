from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import LineEdit, PushButton, TextEdit


class LogPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.search_edit = LineEdit()
        self.search_edit.setPlaceholderText("搜索日志")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.render)
        self.filter_buttons: list[PushButton] = []
        self.current_filter = "全部"

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.search_edit, 1)
        for label in ["全部", "信息", "警告", "错误"]:
            button = PushButton()
            button.setText(label)
            button.clicked.connect(lambda _checked=False, value=label: self.set_filter(value))
            if label == "全部":
                button.setObjectName("primaryButton")
            self.filter_buttons.append(button)
            toolbar.addWidget(button)

        self.text = TextEdit()
        self.text.setReadOnly(True)
        self.export_button = PushButton()
        self.export_button.setText("导出日志")
        self.export_button.setIcon(FIF.DOWNLOAD)
        self.export_button.clicked.connect(self.export_log)
        toolbar.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.addLayout(toolbar)
        layout.addWidget(self.text)

    def set_log(self, lines: list[str]) -> None:
        self.lines = list(lines)
        self.render()

    def append_line(self, line: str) -> None:
        self.lines.append(line)
        self.render()

    def set_filter(self, value: str) -> None:
        self.current_filter = value
        for button in self.filter_buttons:
            button.setObjectName("primaryButton" if button.text() == value else "")
            button.style().unpolish(button)
            button.style().polish(button)
        self.render()

    def render(self) -> None:
        query = self.search_edit.text().strip().lower()
        filtered = []
        for line in self.lines:
            lower = line.lower()
            if query and query not in lower:
                continue
            if self.current_filter == "错误" and "失败" not in line and "error" not in lower and "异常" not in line:
                continue
            if self.current_filter == "警告" and "warning" not in lower and "警告" not in line:
                continue
            if self.current_filter == "信息" and ("失败" in line or "error" in lower or "异常" in line):
                continue
            filtered.append(line)
        self.text.setPlainText("\n".join(filtered))

    def export_log(self) -> None:
        content = self.text.toPlainText()
        if not content.strip():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            str(Path.home() / "epubforge.log"),
            "Log Files (*.log);;Text Files (*.txt)",
        )
        if path:
            Path(path).write_text(content, encoding="utf-8")
