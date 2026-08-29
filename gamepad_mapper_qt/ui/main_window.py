# -*- coding: utf-8 -*-
"""主窗口"""

import os
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox, QComboBox,
)

from core.button_map import IDX_LT, IDX_START
from core.constants import (
    APP_NAME, APP_VERSION, THEME,
    LT_LONG_PRESS_SEC, PROFILE_ORDER, UNIVERSAL_MOUSE_MAPPINGS,
)
from core.autostart import apply_enabled as apply_autostart, is_supported as autostart_supported
from core.config_store import (
    AppState,
    ConfigNotSavable,
    HarnessProfile,
    effective_mappings,
    list_profile_ids,
    load_app_state,
    load_active_profile_id,
    load_profile,
    save_app_state,
    save_active_profile_id,
    save_profile,
)
from core.gamepad_input import GamepadInput
from core.joystick_manager import JoystickManager
from core.keyboard_output import KeyboardOutput
from core.mapping_engine import MappingEngine
from core.mouse_output import MouseOutput
from core.window_focus import focus_process, is_process_foreground
from ui.widgets.gamepad_panel import GamepadPanel
from ui.widgets.mapping_table import MappingTable
from ui.widgets.status_bar import StatusBar
from ui.widgets.key_bind_dialog import KeyBindDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(1100, 780)
        self.resize(1200, 860)

        self._joystick = JoystickManager()
        self._input = GamepadInput(
            self._joystick,
            long_press_after={IDX_LT: LT_LONG_PRESS_SEC},
        )
        self._keyboard = KeyboardOutput()
        self._mouse = MouseOutput()
        self._engine = MappingEngine(self._keyboard, self._mouse)
        self._profile: HarnessProfile | None = None
        self._profile_ids: list[str] = []
        self._mappings: dict[int, str] = {}
        self._threshold = 0.5
        self._gate_open = False
        self._app_state = AppState()
        self._帧计数 = 0
        self._已提示的拒写: set[str] = set()

        self._load_styles()
        self._setup_ui()
        self._connect_signals()
        self._load_app_settings()
        self._load_profiles()
        self._refresh_joystick()
        self._提示损坏方案()   # 必须在 _refresh_joystick 之后，否则会被它冲掉

        # 全应用唯一的 tick：60Hz 采样，面板每两帧重绘一次
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._tick)
        self._poll_timer.start(16)

        QTimer.singleShot(800, self._try_auto_start_mapping)

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

        header = QFrame()
        header.setObjectName("headerFrame")
        header.setFixedHeight(84)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        subtitle = QLabel("Harness / 浏览器 / 通用 · 统一鼠标层")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col)

        header_layout.addStretch()

        harness_label = QLabel("当前方案")
        harness_label.setObjectName("fieldLabel")
        header_layout.addWidget(harness_label)

        self._profile_combo = QComboBox()
        self._profile_combo.setMinimumWidth(200)
        self._profile_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        header_layout.addWidget(self._profile_combo)

        self._gate_dot = QLabel("●")
        self._gate_dot.setObjectName("statusDot")
        self._gate_dot.setStyleSheet(f"color: {THEME['warn']};")
        header_layout.addWidget(self._gate_dot)

        self._gate_label = QLabel("未对准")
        self._gate_label.setObjectName("statusText")
        header_layout.addWidget(self._gate_label)

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

        body = QHBoxLayout()
        body.setContentsMargins(20, 20, 20, 12)
        body.setSpacing(20)

        self._gamepad_panel = GamepadPanel()
        body.addWidget(self._gamepad_panel, stretch=4)

        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        table_header = QHBoxLayout()
        table_header.setSpacing(12)
        table_title = QLabel("按键映射")
        table_title.setObjectName("sectionLabel")
        table_header.addWidget(table_title)
        table_header.addStretch()

        focus_btn = QPushButton("聚焦窗口")
        focus_btn.setObjectName("refreshBtn")
        focus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        focus_btn.clicked.connect(self._focus_current_harness)
        table_header.addWidget(focus_btn)

        clear_all_btn = QPushButton("全部清除")
        clear_all_btn.setObjectName("clearBtn")
        clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_all_btn.clicked.connect(self._clear_all_mappings)
        table_header.addWidget(clear_all_btn)
        right_col.addLayout(table_header)

        self._mapping_table = MappingTable()
        right_col.addWidget(self._mapping_table, stretch=1)

        hint = QLabel(
            "LT 短按聚焦 · LT 长按切方案 · RT 按住语音 · Start 启停映射"
        )
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        right_col.addWidget(hint)

        body.addLayout(right_col, stretch=6)
        root.addLayout(body, stretch=1)

        self._status_bar = StatusBar()
        root.addWidget(self._status_bar)

    def _connect_signals(self):
        self._mapping_table.bind_requested.connect(self._open_bind_dialog)
        self._mapping_table.mapping_changed.connect(self._on_mapping_changed)
        self._status_bar.start_stop_clicked.connect(self._toggle_mapping)
        self._status_bar.threshold_changed.connect(self._on_threshold_changed)
        self._status_bar.mouse_sensitivity_changed.connect(self._on_mouse_sensitivity_changed)
        self._status_bar.scroll_sensitivity_changed.connect(self._on_scroll_sensitivity_changed)
        self._status_bar.launch_at_startup_changed.connect(self._on_launch_at_startup_changed)
        self._status_bar.auto_start_mapping_changed.connect(self._on_auto_start_mapping_changed)

        self._engine.state_changed.connect(self._on_engine_state)
        self._engine.error_occurred.connect(self._on_engine_error)
        self._engine.gate_changed.connect(self._on_gate_changed)

        shortcut = QShortcut(QKeySequence("F9"), self)
        shortcut.activated.connect(self._toggle_mapping)

    def _load_app_settings(self) -> None:
        self._app_state = load_app_state()
        self._status_bar.set_launch_at_startup(self._app_state.launch_at_startup)
        self._status_bar.set_auto_start_mapping(self._app_state.auto_start_mapping)
        if autostart_supported() and self._app_state.launch_at_startup:
            try:
                apply_autostart(True)
            except OSError as exc:
                self._status_bar.set_status(f"自启动注册失败: {exc}")

    def _save_app_settings(self) -> None:
        self._安全保存(lambda: save_app_state(self._app_state))

    def _on_launch_at_startup_changed(self, enabled: bool) -> None:
        if not autostart_supported():
            self._status_bar.set_launch_at_startup(False)
            QMessageBox.warning(self, "提示", "开机自启动目前仅支持 Windows。")
            return
        try:
            apply_autostart(enabled)
        except OSError as exc:
            self._status_bar.set_launch_at_startup(not enabled)
            QMessageBox.warning(self, "自启动失败", str(exc))
            return
        self._app_state.launch_at_startup = enabled
        self._save_app_settings()
        self._status_bar.set_status("已开启开机自启动" if enabled else "已关闭开机自启动")

    def _on_auto_start_mapping_changed(self, enabled: bool) -> None:
        self._app_state.auto_start_mapping = enabled
        self._save_app_settings()
        self._status_bar.set_status("已开启启动后自动映射" if enabled else "已关闭启动后自动映射")

    def _try_auto_start_mapping(self) -> None:
        if not self._app_state.auto_start_mapping or self._engine.is_active:
            return
        if not self._joystick.connected:
            self._joystick.refresh()
        self._start_mapping(silent=True)

    def _load_profiles(self):
        self._profile_ids = list_profile_ids()
        active_id = load_active_profile_id()
        if active_id not in self._profile_ids:
            self._profile_ids = list(PROFILE_ORDER)

        self._profile_combo.blockSignals(True)
        self._profile_combo.clear()
        for pid in self._profile_ids:
            profile = load_profile(pid)
            if profile and not profile.savable:
                label = f"⚠ {pid}（读取失败）"
            elif profile:
                label = profile.display_name
            else:
                label = pid
            self._profile_combo.addItem(label, pid)
        idx = self._profile_ids.index(active_id) if active_id in self._profile_ids else 0
        self._profile_combo.setCurrentIndex(idx)
        self._profile_combo.blockSignals(False)

        self._apply_profile(active_id)

    def _apply_profile(self, profile_id: str) -> None:
        profile = load_profile(profile_id)
        if not profile:
            profile = HarnessProfile(id=profile_id, display_name=profile_id)
        self._profile = profile
        # app_state.json 损坏时这里会拒写；不能让它把切方案和启动一起搞挂
        self._安全保存(lambda: save_active_profile_id(profile_id))

        self._mappings = effective_mappings(profile)
        self._threshold = profile.threshold
        self._joystick.threshold = profile.threshold
        self._mapping_table.load_mappings(self._mappings)
        self._status_bar.set_threshold(profile.threshold)
        self._status_bar.set_mouse_sensitivity(profile.mouse_sensitivity)
        self._status_bar.set_scroll_sensitivity(profile.scroll_sensitivity)
        self._engine.set_mappings(self._mappings)
        self._engine.set_process_names(profile.process_names)
        self._apply_stick_settings(profile)
        self._engine.set_gate_checker(self._check_gate)
        self._update_gate_display()

        self._提示损坏方案()

    def _提示损坏方案(self) -> None:
        """当前方案文件读不了时，把原因写到状态栏

        在 __init__ 末尾要再调一次：_refresh_joystick 会写状态栏，
        否则启动时这条解释会被「手柄已连接」冲掉。
        """
        if self._profile and not self._profile.savable:
            self._status_bar.set_status(
                f"⚠ config/profiles/{self._profile.id}.json 读取失败（JSON 格式有误）。"
                "映射显示为空，已停止写入以免覆盖你原有的配置。修复文件后重启生效。"
            )

    def _apply_stick_settings(self, profile: HarnessProfile) -> None:
        self._engine.set_mouse_settings(
            profile.mouse_sensitivity,
            profile.stick_deadzone,
            profile.scroll_sensitivity,
        )

    def _check_gate(self) -> bool:
        if not self._profile:
            return True
        return is_process_foreground(self._profile.process_names)

    def _update_gate_display(self) -> None:
        open_ = self._check_gate()
        self._gate_open = open_
        name = self._profile.display_name if self._profile else ""
        if self._profile and not self._profile.process_names:
            self._gate_dot.setStyleSheet(f"color: {THEME['accent']};")
            self._gate_label.setText(f"{name} · 任意窗口")
            return
        if open_:
            self._gate_dot.setStyleSheet(f"color: {THEME['accent']};")
            self._gate_label.setText(f"已对准 {name}")
        else:
            self._gate_dot.setStyleSheet(f"color: {THEME['warn']};")
            self._gate_label.setText(f"未对准 {name}")

    def _mappings_for_save(self, table_mappings: dict[int, str]) -> dict[int, str]:
        """保存时去掉与统一鼠标层相同的项，避免每个方案重复写一遍"""
        if not self._profile or not self._profile.universal_mouse:
            return dict(table_mappings)
        saved: dict[int, str] = {}
        for key, value in table_mappings.items():
            if (
                key in UNIVERSAL_MOUSE_MAPPINGS
                and value == UNIVERSAL_MOUSE_MAPPINGS[key]
            ):
                continue
            saved[key] = value
        return saved

    def _on_profile_changed(self, index: int) -> None:
        if index < 0:
            return
        was_running = self._engine.is_active
        if was_running:
            self._engine.stop_mapping()
        self._save_current_profile()
        profile_id = self._profile_combo.itemData(index)
        if profile_id:
            self._apply_profile(profile_id)
        if was_running:
            self._engine.start_mapping()

    def _cycle_profile(self) -> None:
        if not self._profile_ids:
            return
        current_id = self._profile_combo.currentData() or self._profile_ids[0]
        idx = self._profile_ids.index(current_id) if current_id in self._profile_ids else 0
        next_idx = (idx + 1) % len(self._profile_ids)
        self._profile_combo.setCurrentIndex(next_idx)
        self._status_bar.set_status(
            f"已切换 Harness → {self._profile_combo.currentText()}"
        )

    def _focus_current_harness(self) -> None:
        if not self._profile or not self._profile.process_names:
            self._status_bar.set_status("当前方案未配置 process_names")
            return
        if focus_process(self._profile.process_names):
            self._status_bar.set_status(f"已聚焦 {self._profile.display_name}")
        else:
            self._status_bar.set_status(
                f"未找到 {self._profile.display_name} 窗口，请检查 process_names"
            )
        self._update_gate_display()

    def _安全保存(self, 动作) -> bool:
        """执行一次保存；文件读不了时不写入，只提示一次

        六个保存触发点全部经由这里，所以拒写的上报也只需要写在这一处。
        去重是必须的：拖一次滑块会触发几十次保存。
        """
        try:
            动作()
            return True
        except ConfigNotSavable as exc:
            消息 = str(exc)
            if 消息 not in self._已提示的拒写:
                self._已提示的拒写.add(消息)
                self._status_bar.set_status(消息)
            return False

    def _save_current_profile(self) -> None:
        if not self._profile:
            return
        table_mappings = self._mapping_table.get_mappings()
        self._profile.mappings = self._mappings_for_save(table_mappings)
        self._profile.threshold = self._joystick.threshold
        if self._安全保存(lambda: save_profile(self._profile)):
            self._mappings = effective_mappings(self._profile)

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

    def _tick(self):
        """全应用唯一的 tick：一次采样，所有消费者读同一帧"""
        frame = self._input.tick(time.monotonic())
        if not frame.connected:
            return

        self._engine.consume(frame)
        self._分派保留槽位(frame)
        self._更新表格高亮(frame)
        self._update_gate_display()

        self._帧计数 += 1
        if self._帧计数 % 2 == 0:
            self._gamepad_panel.update_state(frame)

    def _分派保留槽位(self, frame) -> None:
        """保留槽位的语义留在这里；边沿判定由 GamepadInput 负责"""
        if IDX_START in frame.just_pressed:
            self._toggle_mapping()
        if IDX_LT in frame.just_long_pressed:
            self._cycle_profile()
        if IDX_LT in frame.just_short_released:
            self._focus_current_harness()

    def _更新表格高亮(self, frame) -> None:
        for slot in frame.just_pressed:
            if slot not in (IDX_LT, IDX_START):
                self._mapping_table.highlight_button(slot)
        for slot in frame.just_released:
            if slot not in (IDX_LT, IDX_START):
                self._mapping_table.clear_highlight_if(slot)

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
        self._save_current_profile()
        self._mapping_table.load_mappings(self._mappings)

    def _on_threshold_changed(self, value: float):
        self._threshold = value
        self._joystick.threshold = value
        if self._profile:
            self._profile.threshold = value
        self._save_current_profile()

    def _on_mouse_sensitivity_changed(self, value: float):
        if self._profile:
            self._profile.mouse_sensitivity = value
            self._apply_stick_settings(self._profile)
        self._save_current_profile()

    def _on_scroll_sensitivity_changed(self, value: float):
        if self._profile:
            self._profile.scroll_sensitivity = value
            self._apply_stick_settings(self._profile)
        self._save_current_profile()

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

    def _start_mapping(self, silent: bool = False):
        mappings = self._mapping_table.get_mappings()
        if not self._joystick.connected:
            if silent:
                self._status_bar.set_status("自动映射：未检测到手柄")
            else:
                QMessageBox.warning(self, "警告", "没有检测到手柄，请先连接并刷新！")
            return
        if not mappings:
            if silent:
                self._status_bar.set_status("自动映射：当前方案无按键映射")
            else:
                QMessageBox.warning(self, "警告", "请先绑定至少一个按键映射！")
            return

        self._engine.set_mappings(mappings)
        self._engine.set_gate_checker(self._check_gate)
        self._engine.start_mapping()
        if silent:
            self._status_bar.set_status("已自动开始映射")
        else:
            self._status_bar.set_status("映射运行中… (F9 / Start 停止)")

    def _on_engine_state(self, running: bool):
        self._status_bar.set_running(running)
        if not running:
            self._status_bar.set_status("已停止")

    def _on_engine_error(self, msg: str):
        self._status_bar.set_status(f"错误: {msg}")

    def _on_gate_changed(self, open_: bool, _label: str):
        self._gate_open = open_
        self._update_gate_display()

    def closeEvent(self, event):
        self._poll_timer.stop()
        self._engine.stop_mapping()
        self._engine.terminate_engine()
        self._save_current_profile()
        self._save_app_settings()
        self._joystick.shutdown()
        event.accept()
