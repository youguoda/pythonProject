# -*- coding: utf-8 -*-
"""可视化手柄面板"""

from typing import List

from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from core.constants import THEME
from core.joystick_manager import PollResult
from core.button_map import IDX_LT, IDX_RT
from core.slots import SLOTS


class GamepadCanvas(QWidget):
    """自定义绘制手柄状态"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pressed: List[bool] = [False] * len(SLOTS)
        self._left_stick = (0.0, 0.0)
        self._right_stick = (0.0, 0.0)
        self._lt = 0.0
        self._rt = 0.0
        self.setMinimumSize(360, 320)

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
        self._draw_trigger(painter, w * 0.18, h * 0.12, w * 0.22, h * 0.06, self._lt, SLOTS[IDX_LT])
        self._draw_trigger(painter, w * 0.60, h * 0.12, w * 0.22, h * 0.06, self._rt, SLOTS[IDX_RT])

        # 摇杆
        self._draw_stick(painter, w * 0.22, h * 0.58, w * 0.09, self._left_stick, "L")
        self._draw_stick(painter, w * 0.72, h * 0.62, w * 0.09, self._right_stick, "R")

        # 全部 24 个槽位由同一张表驱动
        for 槽 in SLOTS:
            px, py, pr = 槽.panel
            pressed = self._pressed[槽.index] if 槽.index < len(self._pressed) else False
            if 槽.render == "button":
                self._draw_button(
                    painter, w * px, h * py, min(w, h) * pr,
                    槽.color, 槽.name.split()[-1], pressed,
                )
            elif pressed:  # dot：摇杆方向指示，按下才画
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
            font = QFont("Segoe UI", max(9, int(r * 0.85)), QFont.Weight.Bold)
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
        font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(QRectF(cx - r, cy + r + 2, r * 2, 18),
                         Qt.AlignmentFlag.AlignCenter, label)

    def _draw_trigger(self, painter, x, y, w, h, value, 槽):
        painter.setPen(QPen(QColor(THEME["border"]), 1))
        painter.setBrush(QBrush(QColor(THEME["dim"])))
        painter.drawRoundedRect(QRectF(x, y, w, h), 4, 4)

        fill_w = w * max(0.0, min(1.0, value))
        if fill_w > 0:
            grad_color = QColor(槽.color)
            painter.setBrush(QBrush(grad_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, fill_w, h), 4, 4)

        painter.setPen(QPen(QColor(THEME["subtext"])))
        font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(QRectF(x, y - 18, w, 16), Qt.AlignmentFlag.AlignCenter, 槽.name)


class GamepadPanel(QFrame):
    """手柄可视化面板容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cardFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("手柄状态")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        self._canvas = GamepadCanvas()
        layout.addWidget(self._canvas, stretch=1)

        self._info = QLabel("未连接")
        self._info.setObjectName("infoLabel")
        self._info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._info)

    def update_state(self, result: PollResult):
        self._canvas.update_state(result)

    def set_info(self, text: str, connected: bool):
        self._info.setText(text)
        色 = THEME["accent"] if connected else THEME["warn"]
        self._info.setStyleSheet(f"color: {色}; font-size: 15px; font-weight: 600;")
