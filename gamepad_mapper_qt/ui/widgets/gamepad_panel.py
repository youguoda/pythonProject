# -*- coding: utf-8 -*-
"""可视化手柄面板"""

from typing import List

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from core.constants import BUTTON_NAMES, BTN_COLOR, DEFAULT_BTN_COLOR, THEME
from core.joystick_manager import PollResult


# 按钮在面板上的布局位置 (x%, y%, radius%)
_BUTTON_LAYOUT = {
    0: (0.62, 0.55, 0.055),   # A
    1: (0.72, 0.45, 0.055),   # B
    2: (0.52, 0.45, 0.055),   # X
    3: (0.62, 0.35, 0.055),   # Y
    4: (0.18, 0.28, 0.045),   # LB
    5: (0.82, 0.28, 0.045),   # RB
    8: (0.38, 0.38, 0.035),   # Back
    9: (0.50, 0.38, 0.035),   # Start
    10: (0.22, 0.58, 0.030),  # L3
    11: (0.72, 0.62, 0.030),  # R3
    12: (0.50, 0.72, 0.030),  # D-Up
    13: (0.50, 0.88, 0.030),  # D-Down
    14: (0.38, 0.80, 0.030),  # D-Left
    15: (0.62, 0.80, 0.030),  # D-Right
}


class GamepadCanvas(QWidget):
    """自定义绘制手柄状态"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pressed: List[bool] = [False] * len(BUTTON_NAMES)
        self._left_stick = (0.0, 0.0)
        self._right_stick = (0.0, 0.0)
        self._lt = 0.0
        self._rt = 0.0
        self.setMinimumSize(320, 280)

    def update_state(self, result: PollResult):
        self._pressed = list(result.pressed)
        self._left_stick = result.left_stick
        self._right_stick = result.right_stick
        self._lt = result.lt_value
        self._rt = result.rt_value
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 背景卡片
        painter.fillRect(self.rect(), QColor(THEME["card"]))

        # 手柄轮廓
        pen = QPen(QColor(THEME["border"]), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(THEME["panel"])))
        body = QRectF(w * 0.08, h * 0.18, w * 0.84, h * 0.62)
        painter.drawRoundedRect(body, 40, 40)

        # 左握把
        painter.drawEllipse(QPointF(w * 0.14, h * 0.72), w * 0.10, h * 0.14)
        # 右握把
        painter.drawEllipse(QPointF(w * 0.86, h * 0.72), w * 0.10, h * 0.14)

        # LT / RT 扳机条
        self._draw_trigger(painter, w * 0.18, h * 0.12, w * 0.22, h * 0.06, self._lt, "LT")
        self._draw_trigger(painter, w * 0.60, h * 0.12, w * 0.22, h * 0.06, self._rt, "RT")

        # 摇杆
        self._draw_stick(painter, w * 0.22, h * 0.58, w * 0.09, self._left_stick, "L")
        self._draw_stick(painter, w * 0.72, h * 0.62, w * 0.09, self._right_stick, "R")

        # 按钮
        for bi, (px, py, pr) in _BUTTON_LAYOUT.items():
            cx, cy, r = w * px, h * py, min(w, h) * pr
            name = BUTTON_NAMES[bi]
            color = BTN_COLOR.get(name, DEFAULT_BTN_COLOR)
            pressed = self._pressed[bi] if bi < len(self._pressed) else False
            self._draw_button(painter, cx, cy, r, color, name.split()[-1], pressed)

        # LT/RT 数字键指示
        for bi in (6, 7):
            val = self._lt if bi == 6 else self._rt
            px, py = (0.28, 0.22) if bi == 6 else (0.72, 0.22)
            pressed = val > 0.5
            name = BUTTON_NAMES[bi]
            color = BTN_COLOR.get(name, DEFAULT_BTN_COLOR)
            self._draw_button(painter, w * px, h * py, min(w, h) * 0.04, color, name, pressed)

        # 摇杆方向指示
        stick_dirs = {
            16: (0.22, 0.48), 17: (0.22, 0.68),
            18: (0.12, 0.58), 19: (0.32, 0.58),
            20: (0.72, 0.52), 21: (0.72, 0.72),
            22: (0.82, 0.62), 23: (0.62, 0.62),
        }
        for bi, (px, py) in stick_dirs.items():
            if self._pressed[bi]:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(THEME["accent"])))
                painter.drawEllipse(QPointF(w * px, h * py), 4, 4)

        painter.end()

    def _draw_button(self, painter, cx, cy, r, color_hex, label, pressed):
        color = QColor(color_hex)
        if pressed:
            grad = QRadialGradient(cx, cy, r * 1.5)
            grad.setColorAt(0, color.lighter(160))
            grad.setColorAt(0.6, color)
            grad.setColorAt(1, color.darker(130))
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(color.lighter(180), 2))
        else:
            painter.setBrush(QBrush(color.darker(150)))
            painter.setPen(QPen(QColor(THEME["border"]), 1))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        if label:
            painter.setPen(QPen(QColor(THEME["dark"] if pressed else THEME["subtext"])))
            font = QFont("Segoe UI", max(7, int(r * 0.7)), QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(QRectF(cx - r, cy - r, r * 2, r * 2),
                             Qt.AlignmentFlag.AlignCenter, label)

    def _draw_stick(self, painter, cx, cy, r, stick_val, label):
        painter.setPen(QPen(QColor(THEME["border"]), 2))
        painter.setBrush(QBrush(QColor(THEME["dim"])))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        sx = cx + stick_val[0] * r * 0.7
        sy = cy + stick_val[1] * r * 0.7
        painter.setBrush(QBrush(QColor(THEME["accent"])))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(sx, sy), r * 0.35, r * 0.35)

        painter.setPen(QPen(QColor(THEME["subtext"])))
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.drawText(QRectF(cx - r, cy + r + 2, r * 2, 14),
                         Qt.AlignmentFlag.AlignCenter, label)

    def _draw_trigger(self, painter, x, y, w, h, value, label):
        painter.setPen(QPen(QColor(THEME["border"]), 1))
        painter.setBrush(QBrush(QColor(THEME["dim"])))
        painter.drawRoundedRect(QRectF(x, y, w, h), 4, 4)

        fill_w = w * max(0.0, min(1.0, value))
        if fill_w > 0:
            grad_color = QColor(BTN_COLOR.get(label, DEFAULT_BTN_COLOR))
            painter.setBrush(QBrush(grad_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, fill_w, h), 4, 4)

        painter.setPen(QPen(QColor(THEME["subtext"])))
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.drawText(QRectF(x, y - 14, w, 12), Qt.AlignmentFlag.AlignCenter, label)


class GamepadPanel(QFrame):
    """手柄可视化面板容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("手柄状态")
        title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {THEME['subtext']};")
        layout.addWidget(title)

        self._canvas = GamepadCanvas()
        layout.addWidget(self._canvas, stretch=1)

        self._info = QLabel("未连接")
        self._info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info.setStyleSheet(f"color: {THEME['subtext']}; font-size: 11px;")
        layout.addWidget(self._info)

    def update_state(self, result: PollResult):
        self._canvas.update_state(result)

    def set_info(self, text: str, connected: bool):
        color = THEME["accent"] if connected else THEME["warn"]
        self._info.setText(text)
        self._info.setStyleSheet(f"color: {color}; font-size: 11px;")
