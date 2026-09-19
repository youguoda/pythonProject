# -*- coding: utf-8 -*-
"""系统托盘

隐藏启动必须配托盘 —— 否则窗口一藏就再也叫不回来，
只能去任务管理器杀进程。
"""

from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap, QBrush, QPen
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from core.constants import APP_NAME, THEME


def _make_icon(running: bool) -> QIcon:
    """画一个手柄轮廓的小图标；映射运行中用强调色，停止时用灰"""
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    色 = QColor(THEME["accent"]) if running else QColor("#6a6a88")
    p.setBrush(QBrush(色))
    p.setPen(QPen(QColor(0, 0, 0, 90), 2))
    # 机身
    p.drawRoundedRect(8, 20, 48, 26, 12, 12)
    # 两侧握把
    p.drawEllipse(6, 28, 22, 26)
    p.drawEllipse(36, 28, 22, 26)
    # 中间挖空一点，让轮廓在小尺寸下能分辨
    p.setBrush(QBrush(QColor(20, 20, 38)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(20, 30, 10, 10)
    p.drawEllipse(34, 30, 10, 10)
    p.end()
    return QIcon(pm)


class Tray(QObject):
    """托盘图标与右键菜单

    只发信号，不直接操作窗口 —— 让 MainWindow 决定怎么响应。
    """

    show_requested = pyqtSignal()
    toggle_mapping_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = QSystemTrayIcon(_make_icon(False), parent)
        self._icon.setToolTip(APP_NAME)

        menu = QMenu()
        显示 = QAction("显示主窗口", menu)
        显示.triggered.connect(self.show_requested)
        menu.addAction(显示)

        self._toggle_action = QAction("启动映射", menu)
        self._toggle_action.triggered.connect(self.toggle_mapping_requested)
        menu.addAction(self._toggle_action)

        menu.addSeparator()
        退出 = QAction("退出", menu)
        退出.triggered.connect(self.quit_requested)
        menu.addAction(退出)

        self._icon.setContextMenu(menu)
        self._icon.activated.connect(self._on_activated)
        self._menu = menu

    def _on_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.show_requested.emit()

    def show(self):
        self._icon.show()

    def hide(self):
        self._icon.hide()

    def set_running(self, running: bool):
        """映射启停时更新图标与菜单文字"""
        self._icon.setIcon(_make_icon(running))
        self._toggle_action.setText("停止映射" if running else "启动映射")
        self._icon.setToolTip(f"{APP_NAME} — {'映射中' if running else '已停止'}")

    def notify(self, 消息: str):
        if self._icon.supportsMessages():
            self._icon.showMessage(APP_NAME, 消息, _make_icon(False), 3000)
