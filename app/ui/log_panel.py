from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QPushButton, QTextEdit, QVBoxLayout, QWidget


class LogPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.export_button = QPushButton("导出日志")
        self.export_button.clicked.connect(self.export_log)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text)
        layout.addWidget(self.export_button)

    def set_log(self, lines: list[str]) -> None:
        self.text.setPlainText("\n".join(lines))

    def append_line(self, line: str) -> None:
        self.text.append(line)

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

