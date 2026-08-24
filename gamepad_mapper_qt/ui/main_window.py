# -*- coding: utf-8 -*-
"""主窗口"""

import os

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox,
)

from core.constants import APP_NAME, APP_VERSION, THEME, BUTTON_NAMES
from core.config_store import load_config, save_config
from core.joystick_manager import JoystickManager
from core.keyboard_output import KeyboardOutput
from core.mapping_engine import MappingEngine
from ui.widgets.gamepad_panel import GamepadPanel
from ui.widgets.mapping_table import MappingTable
from ui.widgets.status_bar import StatusBar
from ui.widgets.key_bind_dialog import KeyBindDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(960, 640)
        self.resize(1060, 720)

        self._joystick = JoystickManager()
        self._keyboard = KeyboardOutput()
        self._engine = MappingEngine(self._joystick, self._keyboard)
        self._mappings: dict[int, str] = {}
        self._threshold = 0.5
        self._prev_pressed = [False] * len(BUTTON_NAMES)

        self._load_styles()
        self._setup_ui()
        self._connect_signals()
        self._load_saved_config()
        self._refresh_joystick()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_visual)
        self._poll_timer.start(30)

        self._engine.start()

    def _load_styles(self):
        style_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "styles", "theme.qss"
        )
        if os.path.isfile(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("headerFrame")
        header.setFixedHeight(64)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        subtitle = QLabel("手柄按键 → 键盘映射")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col)

        header_layout.addStretch()

        self._conn_dot = QLabel("●")
        self._conn_dot.setObjectName("statusDot")
        self._conn_dot.setStyleSheet(f"color: {THEME['warn']};")
        header_layout.addWidget(self._conn_dot)

        self._conn_label = QLabel("未连接")
        self._conn_label.setObjectName("statusText")
        header_layout.addWidget(self._conn_label)

        refresh_btn = QPushButton("⟳  刷新")
        refresh_btn.setObjectName("refreshBtn")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_joystick)
        header_layout.addWidget(refresh_btn)

        root.addWidget(header)

        # Body
        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 8)
        body.setSpacing(16)

        self._gamepad_panel = GamepadPanel()
        body.addWidget(self._gamepad_panel, stretch=4)

        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        table_header = QHBoxLayout()
        table_title = QLabel("按键映射")
        table_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {THEME['subtext']};")
        table_header.addWidget(table_title)
        table_header.addStretch()

        clear_all_btn = QPushButton("全部清除")
        clear_all_btn.setObjectName("clearBtn")
        clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_all_btn.clicked.connect(self._clear_all_mappings)
        table_header.addWidget(clear_all_btn)
        right_col.addLayout(table_header)

        self._mapping_table = MappingTable()
        right_col.addWidget(self._mapping_table, stretch=1)

        body.addLayout(right_col, stretch=6)
        root.addLayout(body, stretch=1)

        # Footer
        self._status_bar = StatusBar()
        root.addWidget(self._status_bar)

    def _connect_signals(self):
        self._mapping_table.bind_requested.connect(self._open_bind_dialog)
        self._mapping_table.mapping_changed.connect(self._on_mapping_changed)
        self._status_bar.start_stop_clicked.connect(self._toggle_mapping)
        self._status_bar.threshold_changed.connect(self._on_threshold_changed)

        self._engine.state_changed.connect(self._on_engine_state)
        self._engine.error_occurred.connect(self._on_engine_error)

        shortcut = QShortcut(QKeySequence("F9"), self)
        shortcut.activated.connect(self._toggle_mapping)

    def _load_saved_config(self):
        mappings, threshold = load_config()
        self._mappings = mappings
        self._threshold = threshold
        self._joystick.threshold = threshold
        self._mapping_table.load_mappings(mappings)
        self._status_bar.set_threshold(threshold)
        self._engine.set_mappings(mappings)

    def _save_config(self):
        save_config(self._mapping_table.get_mappings(), self._joystick.threshold)

    def _refresh_joystick(self):
        if self._engine.is_active:
            self._engine.stop_mapping()

        connected = self._joystick.refresh()
        if connected:
            name = self._joystick.name
            self._conn_dot.setStyleSheet(f"color: {THEME['accent']};")
            self._conn_label.setText(f"已连接: {name[:24]}")
            self._gamepad_panel.set_info(name, True)
            self._status_bar.set_status("手柄已连接")
        else:
            self._conn_dot.setStyleSheet(f"color: {THEME['warn']};")
            self._conn_label.setText("未连接")
            self._gamepad_panel.set_info("未检测到手柄", False)
            self._status_bar.set_status("请连接手柄后点击刷新")

    def _poll_visual(self):
        if not self._joystick.connected:
            return

        result = self._joystick.poll()
        self._gamepad_panel.update_state(result)

        for bi, pressed in enumerate(result.pressed):
            if pressed and not self._prev_pressed[bi]:
                self._mapping_table.highlight_button(bi)
            elif not pressed and self._prev_pressed[bi]:
                self._mapping_table.clear_highlight_if(bi)
            self._prev_pressed[bi] = pressed

    def _open_bind_dialog(self, button_index: int):
        if self._engine.is_active:
            QMessageBox.warning(self, "提示", "请先停止映射，再进行按键绑定。")
            return
        dialog = KeyBindDialog(button_index, self)
        dialog.key_bound.connect(self._on_key_bound)
        dialog.exec()

    def _on_key_bound(self, button_index: int, key_name: str):
        self._mapping_table.set_mapping(button_index, key_name)

    def _on_mapping_changed(self):
        mappings = self._mapping_table.get_mappings()
        self._mappings = mappings
        self._engine.set_mappings(mappings)
        self._save_config()

    def _on_threshold_changed(self, value: float):
        self._threshold = value
        self._joystick.threshold = value
        self._save_config()

    def _clear_all_mappings(self):
        if self._engine.is_active:
            QMessageBox.warning(self, "提示", "请先停止映射。")
            return
        reply = QMessageBox.question(
            self, "确认", "清除所有按键映射？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._mapping_table.clear_all()

    def _toggle_mapping(self):
        if self._engine.is_active:
            self._engine.stop_mapping()
        else:
            self._start_mapping()

    def _start_mapping(self):
        mappings = self._mapping_table.get_mappings()
        if not self._joystick.connected:
            QMessageBox.warning(self, "警告", "没有检测到手柄，请先连接并刷新！")
            return
        if not mappings:
            QMessageBox.warning(self, "警告", "请先绑定至少一个按键映射！")
            return

        self._engine.set_mappings(mappings)
        self._engine.start_mapping()
        self._status_bar.set_status("映射运行中… (F9 停止)")

    def _on_engine_state(self, running: bool):
        self._status_bar.set_running(running)
        if not running:
            self._status_bar.set_status("已停止")

    def _on_engine_error(self, msg: str):
        self._status_bar.set_status(f"错误: {msg}")

    def closeEvent(self, event):
        self._poll_timer.stop()
        self._engine.stop_mapping()
        self._engine.terminate_engine()
        self._save_config()
        self._joystick.shutdown()
        event.accept()
