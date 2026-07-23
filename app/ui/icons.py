from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF


def toolbar_icon(name: str, color: str = "#111827") -> QIcon:
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor(color), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if name == "file":
        painter.drawRect(QRectF(6, 4, 10, 16))
        painter.drawLine(QPointF(13, 4), QPointF(18, 9))
        painter.drawLine(QPointF(13, 4), QPointF(13, 9))
        painter.drawLine(QPointF(13, 9), QPointF(18, 9))
        painter.drawLine(QPointF(17, 15), QPointF(21, 15))
        painter.drawLine(QPointF(19, 13), QPointF(19, 17))
    elif name == "folder":
        path = QPainterPath()
        path.moveTo(3, 7)
        path.lineTo(9, 7)
        path.lineTo(11, 10)
        path.lineTo(21, 10)
        path.lineTo(21, 19)
        path.lineTo(3, 19)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == "folder-plus":
        path = QPainterPath()
        path.moveTo(3, 7)
        path.lineTo(9, 7)
        path.lineTo(11, 10)
        path.lineTo(21, 10)
        path.lineTo(21, 19)
        path.lineTo(3, 19)
        path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(QPointF(16, 13), QPointF(16, 17))
        painter.drawLine(QPointF(14, 15), QPointF(18, 15))
    elif name == "play":
        painter.setBrush(QColor(color))
        painter.drawPolygon(QPolygonF([QPointF(8, 5), QPointF(19, 12), QPointF(8, 19)]))
    elif name == "pause":
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(QRectF(7, 5, 3, 14), 1, 1)
        painter.drawRoundedRect(QRectF(14, 5, 3, 14), 1, 1)
    elif name == "stop":
        painter.setBrush(QColor(color))
        painter.drawRoundedRect(QRectF(7, 7, 10, 10), 1, 1)
    elif name == "retry":
        painter.drawArc(QRectF(5, 5, 14, 14), 30 * 16, 300 * 16)
        painter.drawLine(QPointF(18, 5), QPointF(18, 10))
        painter.drawLine(QPointF(18, 5), QPointF(13, 5))
    elif name == "settings":
        painter.drawEllipse(QPointF(12, 12), 3.2, 3.2)
        for x1, y1, x2, y2 in [
            (12, 3, 12, 6),
            (12, 18, 12, 21),
            (3, 12, 6, 12),
            (18, 12, 21, 12),
            (5.7, 5.7, 7.8, 7.8),
            (16.2, 16.2, 18.3, 18.3),
            (18.3, 5.7, 16.2, 7.8),
            (7.8, 16.2, 5.7, 18.3),
        ]:
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    elif name == "trash":
        painter.drawLine(QPointF(7, 8), QPointF(17, 8))
        painter.drawLine(QPointF(10, 5), QPointF(14, 5))
        painter.drawRect(QRectF(8, 8, 8, 12))
        painter.drawLine(QPointF(10.5, 11), QPointF(10.5, 17))
        painter.drawLine(QPointF(13.5, 11), QPointF(13.5, 17))
    else:
        painter.drawEllipse(QPointF(12, 12), 7, 7)

    painter.end()
    return QIcon(pixmap)
