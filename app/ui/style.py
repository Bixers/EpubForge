from __future__ import annotations

from PySide6.QtGui import QColor, QPalette


def apply_light_palette(app) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#111827"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#1463ff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#94a3b8"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#94a3b8"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#94a3b8"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor("#f1f5f9"))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor("#f1f5f9"))
    app.setPalette(palette)


APP_STYLESHEET = """
* {
  font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
  font-size: 13px;
}
QMainWindow {
  background: #f8fafc;
  color: #111827;
}
QDialog, QMessageBox,
QDialog QWidget, QMessageBox QWidget {
  background: #ffffff;
  color: #111827;
}
QDialog QLabel, QMessageBox QLabel {
  color: #1f2937;
  font-weight: 600;
}
QDialog QLineEdit, QDialog QTextEdit, QDialog QPlainTextEdit, QDialog QComboBox, QDialog QSpinBox {
  background: #ffffff;
  color: #111827;
  border: 1px solid #d5dde8;
  border-radius: 6px;
  selection-background-color: #e7f0ff;
  selection-color: #0f52d9;
}
QDialog QComboBox QAbstractItemView {
  background: #ffffff;
  color: #111827;
  border: 1px solid #d5dde8;
  selection-background-color: #e7f0ff;
  selection-color: #0f52d9;
}
QToolTip {
  background: #ffffff;
  color: #111827;
  border: 1px solid #d5dde8;
  padding: 4px 6px;
}
QMessageBox QPushButton, QDialog QPushButton {
  background: #ffffff;
  color: #111827;
  border: 1px solid #d5dde8;
  border-radius: 6px;
  min-height: 30px;
  padding: 4px 14px;
}
QMessageBox QPushButton:hover, QDialog QPushButton:hover {
  border-color: #2563eb;
  color: #0f52d9;
}
QCheckBox {
  color: #111827;
}
QToolBar {
  background: #ffffff;
  border: 0;
  border-bottom: 1px solid #d8e0ea;
  spacing: 8px;
  padding: 10px 14px;
}
QTableView, QTableWidget, QTreeWidget {
  background: #ffffff;
  border: 0;
  color: #111827;
  selection-background-color: #e7f0ff;
  selection-color: #0f52d9;
}
QTableView::viewport, QTableWidget::viewport {
  background: #ffffff;
}
QTableWidget[emptyState="true"] {
  gridline-color: #f8fafc;
  alternate-background-color: #ffffff;
}
QTableWidget {
  gridline-color: #edf1f6;
  alternate-background-color: #fbfdff;
}
QTableWidget::item, QTreeWidget::item {
  min-height: 28px;
  padding: 3px 8px;
}
QTableWidget::item:hover, QTreeWidget::item:hover {
  background: #f3f4f6;
  color: #111827;
}
QTableWidget::item:selected, QTreeWidget::item:selected {
  background: #e7f0ff;
  color: #0f52d9;
}
QHeaderView::section {
  background: #ffffff;
  border: 0;
  border-bottom: 1px solid #e2e8f0;
  color: #111827;
  font-weight: 700;
  padding: 9px 10px;
}
QTabWidget::pane {
  border: 0;
  background: #ffffff;
}
QTabBar::tab {
  background: #ffffff;
  border: 0;
  border-bottom: 2px solid transparent;
  color: #334155;
  min-width: 118px;
  padding: 12px 18px;
}
QTabBar::tab:selected {
  background: #ffffff;
  color: #0f52d9;
  border-bottom: 2px solid #2563eb;
  font-weight: 700;
}
QFrame#panelFrame, QLabel#coverPreview {
  background: #ffffff;
  border: 1px solid #d5dde8;
  border-radius: 8px;
}
QFrame#emptyDropPanel {
  background: #ffffff;
  border: 2px dashed #d5dde8;
  border-radius: 12px;
}
QLabel#emptyDropTitle {
  color: #475569;
  font-size: 15px;
  font-weight: 600;
}
QLabel#emptyDropSubtitle {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}
QLabel#coverPreview {
  color: #64748b;
}
QLabel#coverFileName {
  color: #111827;
  font-weight: 700;
}
QLabel#coverPathHint {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}
QLabel#statusBadge {
  border-radius: 11px;
  padding-left: 8px;
  padding-right: 8px;
  font-size: 12px;
  font-weight: 700;
}
QLabel#statusBadge[status="waiting"], QLabel#statusBadge[status="running"] {
  background: #e8f1ff;
  color: #0f52d9;
}
QLabel#statusBadge[status="success"] {
  background: #dcfce7;
  color: #15803d;
}
QLabel#statusBadge[status="error"] {
  background: #fee2e2;
  color: #b91c1c;
}
QLabel#statusBadge[status="muted"] {
  background: #f1f5f9;
  color: #475569;
}
QLabel {
  color: #1f2937;
  font-weight: 600;
}
QSplitter::handle {
  background: #e6edf5;
}
QSplitter::handle:hover {
  background: #c7d7ea;
}
QSplitter::handle:horizontal {
  width: 10px;
}
QSplitter::handle:vertical {
  height: 10px;
}
QStatusBar {
  background: #ffffff;
  color: #334155;
  border-top: 1px solid #d8e0ea;
  padding-left: 12px;
  padding-right: 14px;
  font-size: 12px;
}
QLabel#summaryLabel {
  color: #1f2937;
  font-size: 12px;
  font-weight: 600;
  padding-right: 14px;
}
"""
