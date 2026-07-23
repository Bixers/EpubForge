from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import IconWidget, PrimaryPushButton, PushButton, TableWidget

from app.core.models import ConvertTask


class TaskTable(TableWidget):
    import_files_requested = Signal()
    import_folder_requested = Signal()

    HEADERS = ["", "文件名", "格式", "大小", "状态", "进度", "输出路径", "错误信息"]

    def __init__(self) -> None:
        super().__init__()
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(0, 34)
        self.empty_panel = self._create_empty_panel()
        self.refresh_empty_state()

    def _create_empty_panel(self) -> QFrame:
        panel = QFrame(self.viewport())
        panel.setObjectName("emptyDropPanel")
        panel.setFixedSize(520, 230)

        icon = IconWidget(FIF.FOLDER)
        icon.setFixedSize(54, 54)

        title = QLabel("拖入 TXT/EPUB 文件或选择文件夹")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("emptyDropTitle")

        file_button = PrimaryPushButton()
        file_button.setText("选择文件")
        file_button.setIcon(FIF.DOCUMENT)
        file_button.clicked.connect(self.import_files_requested.emit)

        folder_button = PushButton()
        folder_button.setText("选择文件夹")
        folder_button.setIcon(FIF.FOLDER_ADD)
        folder_button.clicked.connect(self.import_folder_requested.emit)

        buttons = QHBoxLayout()
        buttons.setSpacing(18)
        buttons.addStretch(1)
        buttons.addWidget(file_button)
        buttons.addWidget(folder_button)
        buttons.addStretch(1)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(32, 26, 32, 26)
        layout.setSpacing(18)
        layout.addStretch(1)
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addLayout(buttons)
        layout.addStretch(1)
        return panel

    def add_task(self, task: ConvertTask) -> int:
        row = self.rowCount()
        self.insertRow(row)
        self.setVerticalHeaderItem(row, QTableWidgetItem(task.id))
        self.update_task(row, task)
        self.refresh_empty_state()
        return row

    def setRowCount(self, rows: int) -> None:  # noqa: N802 - Qt override
        super().setRowCount(rows)
        self.refresh_empty_state()

    def update_task(self, row: int, task: ConvertTask) -> None:
        values = [
            "",
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
            if column == 0:
                item.setCheckState(Qt.CheckState.Checked)
                item.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )
            if column == 4:
                self._style_status_item(item, task.status)
        self.refresh_empty_state()

    def refresh_empty_state(self) -> None:
        if not hasattr(self, "empty_panel"):
            return
        self.empty_panel.setVisible(self.rowCount() == 0)
        self._position_empty_panel()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._position_empty_panel()

    def _position_empty_panel(self) -> None:
        viewport = self.viewport()
        x = max(24, (viewport.width() - self.empty_panel.width()) // 2)
        y = max(120, (viewport.height() - self.empty_panel.height()) // 2)
        self.empty_panel.move(x, y)

    def _style_status_item(self, item: QTableWidgetItem, status: str) -> None:
        colors = {
            "等待中": (QColor("#e8f1ff"), QColor("#0f52d9")),
            "解析中": (QColor("#e8f1ff"), QColor("#0f52d9")),
            "清洗中": (QColor("#e8f1ff"), QColor("#0f52d9")),
            "生成目录中": (QColor("#e8f1ff"), QColor("#0f52d9")),
            "生成 EPUB 中": (QColor("#e8f1ff"), QColor("#0f52d9")),
            "校验中": (QColor("#e8f1ff"), QColor("#0f52d9")),
            "完成": (QColor("#dcfce7"), QColor("#15803d")),
            "失败": (QColor("#fee2e2"), QColor("#b91c1c")),
            "已取消": (QColor("#f1f5f9"), QColor("#475569")),
        }
        background, foreground = colors.get(status, (QColor("#ffffff"), QColor("#111827")))
        item.setBackground(background)
        item.setForeground(foreground)

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
