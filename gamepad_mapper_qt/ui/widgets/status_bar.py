# -*- coding: utf-8 -*-
"""底部状态栏"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.constants import (
    DEFAULT_MOUSE_SENSITIVITY,
    DEFAULT_SCROLL_SENSITIVITY,
    DEFAULT_THRESHOLD,
    MOUSE_SENSITIVITY_MAX,
    MOUSE_SENSITIVITY_MIN,
    SCROLL_SENSITIVITY_MAX,
    SCROLL_SENSITIVITY_MIN,
)


class StatusBar(QFrame):
    """底部控制栏"""

    start_stop_clicked = pyqtSignal()
    threshold_changed = pyqtSignal(float)
    mouse_sensitivity_changed = pyqtSignal(float)
    scroll_sensitivity_changed = pyqtSignal(float)
    launch_at_startup_changed = pyqtSignal(bool)
    auto_start_mapping_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("footerFrame")
        self.setFixedHeight(168)
        self._running = False
        self._setup_ui()

    def _slider_row(
        self,
        label: str,
        slider: QSlider,
        value_label: QLabel,
    ) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        text = QLabel(label)
        text.setObjectName("sliderLabel")
        layout.addWidget(text)
        layout.addWidget(slider)
        value_label.setObjectName("sliderValue")
        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(value_label)
        return widget

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 12, 24, 12)
        root.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(20)

        self._start_btn = QPushButton("▶  启动映射")
        self._start_btn.setObjectName("startBtn")
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self.start_stop_clicked.emit)
        top.addWidget(self._start_btn)

        top.addStretch()

        self._status_label = QLabel("状态: 就绪")
        self._status_label.setObjectName("statusText")
        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        top.addWidget(self._status_label)

        hint = QLabel("F9 切换映射")
        hint.setObjectName("hintLabel")
        top.addWidget(hint)
        root.addLayout(top)

        options = QHBoxLayout()
        options.setSpacing(24)

        self._launch_checkbox = QCheckBox("开机自启动")
        self._launch_checkbox.setObjectName("optionCheck")
        self._launch_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_checkbox.toggled.connect(self.launch_at_startup_changed.emit)
        options.addWidget(self._launch_checkbox)

        self._auto_map_checkbox = QCheckBox("启动后自动开始映射")
        self._auto_map_checkbox.setObjectName("optionCheck")
        self._auto_map_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self._auto_map_checkbox.toggled.connect(self.auto_start_mapping_changed.emit)
        options.addWidget(self._auto_map_checkbox)

        options.addStretch()
        root.addLayout(options)

        bottom = QHBoxLayout()
        bottom.setSpacing(20)

        self._mouse_slider = QSlider(Qt.Orientation.Horizontal)
        self._mouse_slider.setRange(
            int(MOUSE_SENSITIVITY_MIN), int(MOUSE_SENSITIVITY_MAX)
        )
        self._mouse_slider.setValue(int(DEFAULT_MOUSE_SENSITIVITY))
        self._mouse_slider.setFixedWidth(160)
        self._mouse_slider.valueChanged.connect(self._on_mouse_sensitivity)
        self._mouse_value = QLabel(f"{DEFAULT_MOUSE_SENSITIVITY:.0f}")
        bottom.addWidget(
            self._slider_row("左摇杆鼠标", self._mouse_slider, self._mouse_value)
        )

        self._scroll_slider = QSlider(Qt.Orientation.Horizontal)
        self._scroll_slider.setRange(
            int(SCROLL_SENSITIVITY_MIN * 10), int(SCROLL_SENSITIVITY_MAX * 10)
        )
        self._scroll_slider.setValue(int(DEFAULT_SCROLL_SENSITIVITY * 10))
        self._scroll_slider.setFixedWidth(160)
        self._scroll_slider.valueChanged.connect(self._on_scroll_sensitivity)
        self._scroll_value = QLabel(f"{DEFAULT_SCROLL_SENSITIVITY:.1f}")
        bottom.addWidget(
            self._slider_row("右摇杆滚轮", self._scroll_slider, self._scroll_value)
        )

        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setRange(10, 90)
        self._threshold_slider.setValue(int(DEFAULT_THRESHOLD * 100))
        self._threshold_slider.setFixedWidth(160)
        self._threshold_slider.valueChanged.connect(self._on_threshold)
        self._thr_value = QLabel(f"{DEFAULT_THRESHOLD:.1f}")
        bottom.addWidget(
            self._slider_row("摇杆阈值", self._threshold_slider, self._thr_value)
        )

        bottom.addStretch()
        root.addLayout(bottom)

    def _on_threshold(self, value: int):
        thr = value / 100.0
        self._thr_value.setText(f"{thr:.1f}")
        self.threshold_changed.emit(thr)

    def _on_mouse_sensitivity(self, value: int):
        self._mouse_value.setText(f"{value:.0f}")
        self.mouse_sensitivity_changed.emit(float(value))

    def _on_scroll_sensitivity(self, value: int):
        scroll = value / 10.0
        self._scroll_value.setText(f"{scroll:.1f}")
        self.scroll_sensitivity_changed.emit(scroll)

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

    def set_mouse_sensitivity(self, value: float):
        clamped = max(MOUSE_SENSITIVITY_MIN, min(MOUSE_SENSITIVITY_MAX, value))
        self._mouse_slider.blockSignals(True)
        self._mouse_slider.setValue(int(clamped))
        self._mouse_value.setText(f"{clamped:.0f}")
        self._mouse_slider.blockSignals(False)

    def set_scroll_sensitivity(self, value: float):
        clamped = max(SCROLL_SENSITIVITY_MIN, min(SCROLL_SENSITIVITY_MAX, value))
        self._scroll_slider.blockSignals(True)
        self._scroll_slider.setValue(int(clamped * 10))
        self._scroll_value.setText(f"{clamped:.1f}")
        self._scroll_slider.blockSignals(False)

    def set_launch_at_startup(self, enabled: bool) -> None:
        self._launch_checkbox.blockSignals(True)
        self._launch_checkbox.setChecked(enabled)
        self._launch_checkbox.blockSignals(False)

    def set_auto_start_mapping(self, enabled: bool) -> None:
        self._auto_map_checkbox.blockSignals(True)
        self._auto_map_checkbox.setChecked(enabled)
        self._auto_map_checkbox.blockSignals(False)

    def set_auto_start_mapping_enabled(self, enabled: bool) -> None:
        self._auto_map_checkbox.setEnabled(enabled)
