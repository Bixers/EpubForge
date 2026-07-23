from __future__ import annotations


APP_STYLESHEET = """
* {
  font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
  font-size: 13px;
}
QMainWindow {
  background: #f8fafc;
  color: #111827;
}
QToolBar {
  background: #ffffff;
  border: 0;
  border-bottom: 1px solid #d8e0ea;
  spacing: 8px;
  padding: 12px 14px;
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
QTableWidget {
  gridline-color: #edf1f6;
  alternate-background-color: #fbfdff;
}
QTableWidget::item, QTreeWidget::item {
  min-height: 30px;
  padding: 4px 8px;
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
QLabel#coverPreview {
  color: #64748b;
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
  width: 6px;
}
QSplitter::handle:vertical {
  height: 6px;
}
QStatusBar {
  background: #ffffff;
  color: #334155;
  border-top: 1px solid #d8e0ea;
}
"""
