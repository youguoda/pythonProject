# -*- coding: utf-8 -*-
"""底部状态栏"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

from core.constants import THEME, DEFAULT_THRESHOLD


class StatusBar(QFrame):
    """底部控制栏"""

    start_stop_clicked = pyqtSignal()
    threshold_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("footerFrame")
        self.setFixedHeight(72)
        self._running = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)

        self._start_btn = QPushButton("▶  启动映射")
        self._start_btn.setObjectName("startBtn")
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self.start_stop_clicked.emit)
        layout.addWidget(self._start_btn)

        layout.addStretch()

        # 摇杆阈值
        thr_widget = QWidget()
        thr_layout = QHBoxLayout(thr_widget)
        thr_layout.setContentsMargins(0, 0, 0, 0)
        thr_layout.setSpacing(8)

        thr_label = QLabel("摇杆阈值")
        thr_label.setStyleSheet(f"color: {THEME['subtext']}; font-size: 11px;")
        thr_layout.addWidget(thr_label)

        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setRange(10, 90)
        self._threshold_slider.setValue(int(DEFAULT_THRESHOLD * 100))
        self._threshold_slider.setFixedWidth(120)
        self._threshold_slider.valueChanged.connect(self._on_threshold)
        thr_layout.addWidget(self._threshold_slider)

        self._thr_value = QLabel(f"{DEFAULT_THRESHOLD:.1f}")
        self._thr_value.setStyleSheet(f"color: {THEME['accent']}; font-size: 11px; min-width: 28px;")
        thr_layout.addWidget(self._thr_value)

        layout.addWidget(thr_widget)

        self._status_label = QLabel("状态: 就绪")
        self._status_label.setObjectName("statusText")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._status_label)

        hint = QLabel("F9 切换映射")
        hint.setStyleSheet(f"color: {THEME['dim']}; font-size: 10px;")
        layout.addWidget(hint)

    def _on_threshold(self, value: int):
        thr = value / 100.0
        self._thr_value.setText(f"{thr:.1f}")
        self.threshold_changed.emit(thr)

    def set_running(self, running: bool):
        self._running = running
        if running:
            self._start_btn.setText("■  停止映射")
            self._start_btn.setProperty("running", True)
        else:
            self._start_btn.setText("▶  启动映射")
            self._start_btn.setProperty("running", False)
        self._start_btn.style().unpolish(self._start_btn)
        self._start_btn.style().polish(self._start_btn)

    def set_status(self, text: str):
        self._status_label.setText(f"状态: {text}")

    def set_threshold(self, value: float):
        self._threshold_slider.blockSignals(True)
        self._threshold_slider.setValue(int(value * 100))
        self._thr_value.setText(f"{value:.1f}")
        self._threshold_slider.blockSignals(False)
