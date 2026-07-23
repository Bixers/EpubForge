from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from app.core.models import ConvertTask


class TaskTable(QTableWidget):
    HEADERS = ["文件名", "格式", "大小", "状态", "进度", "输出路径", "错误信息"]

    def __init__(self) -> None:
        super().__init__(0, len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

    def add_task(self, task: ConvertTask) -> int:
        row = self.rowCount()
        self.insertRow(row)
        self.setVerticalHeaderItem(row, QTableWidgetItem(task.id))
        self.update_task(row, task)
        return row

    def update_task(self, row: int, task: ConvertTask) -> None:
        values = [
            task.source_path.name,
            task.source_format.upper(),
            self._format_size(task.file_size),
            task.status,
            f"{task.progress}%",
            str(task.output_path),
            task.error_message,
        ]
        for column, value in enumerate(values):
            item = self.item(row, column)
            if item is None:
                item = QTableWidgetItem()
                self.setItem(row, column, item)
            item.setText(value)
            item.setToolTip(value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def selected_row(self) -> int:
        selected = self.selectionModel().selectedRows()
        return selected[0].row() if selected else -1

    def task_id_at(self, row: int) -> str:
        item = self.verticalHeaderItem(row)
        return item.text() if item else ""

    def _format_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / 1024 / 1024:.1f} MB"

