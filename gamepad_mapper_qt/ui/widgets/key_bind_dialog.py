# -*- coding: utf-8 -*-
"""按键绑定弹窗 — 支持组合键与左右修饰键捕获"""

import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit,
)

from core.slots import SLOTS
from ui.widgets.key_catalog import CATALOG, MOUSE_ACTIONS

# Qt key → pynput-style name
_QT_KEY_MAP = {
    Qt.Key.Key_Space: "space",
    Qt.Key.Key_Return: "enter",
    Qt.Key.Key_Enter: "enter",
    Qt.Key.Key_Tab: "tab",
    Qt.Key.Key_Backspace: "backspace",
    Qt.Key.Key_Delete: "delete",
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
    Qt.Key.Key_Up: "up",
    Qt.Key.Key_Down: "down",
    Qt.Key.Key_F1: "f1", Qt.Key.Key_F2: "f2", Qt.Key.Key_F3: "f3",
    Qt.Key.Key_F4: "f4", Qt.Key.Key_F5: "f5", Qt.Key.Key_F6: "f6",
    Qt.Key.Key_F7: "f7", Qt.Key.Key_F8: "f8", Qt.Key.Key_F9: "f9",
    Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
    Qt.Key.Key_BracketLeft: "[",
    Qt.Key.Key_BracketRight: "]",
    Qt.Key.Key_Semicolon: ";",
    Qt.Key.Key_Apostrophe: "'",
    Qt.Key.Key_Comma: ",",
    Qt.Key.Key_Period: ".",
    Qt.Key.Key_Slash: "/",
    Qt.Key.Key_Backslash: "\\",
    Qt.Key.Key_Minus: "-",
    Qt.Key.Key_Equal: "=",
    Qt.Key.Key_QuoteLeft: "`",
}

_MODIFIER_KEYS = {
    Qt.Key.Key_Shift: "shift",
    Qt.Key.Key_Control: "ctrl",
    Qt.Key.Key_Alt: "alt",
    Qt.Key.Key_Meta: "cmd",
    Qt.Key.Key_Super_L: "cmd",
    Qt.Key.Key_Super_R: "cmd_r",
}

# Windows virtual-key codes for left/right modifiers
_WIN_VK_TO_MOD = {
    0x5B: "cmd_l",
    0x5C: "cmd_r",
    0xA2: "ctrl_l",
    0xA3: "ctrl_r",
    0xA0: "shift_l",
    0xA1: "shift_r",
    0xA4: "alt_l",
    0xA5: "alt_r",
}

_MODIFIER_ORDER = (
    "cmd_l", "cmd_r", "cmd", "win", "super",
    "ctrl_l", "ctrl_r", "ctrl",
    "shift_l", "shift_r", "shift",
    "alt_l", "alt_r", "alt",
)

_DISPLAY_NAMES = {
    "cmd_l": "Win",
    "cmd_r": "Right Win",
    "cmd": "Win",
    "win": "Win",
    "super": "Win",
    "ctrl_l": "Left Ctrl",
    "ctrl_r": "Right Ctrl",
    "shift_l": "Left Shift",
    "shift_r": "Right Shift",
    "alt_l": "Left Alt",
    "alt_r": "Right Alt",
    "ctrl": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
}


# Windows scan codes (extended keys) — fallback when VK is generic
_WIN_SCAN_TO_MOD = {
    29: "ctrl_l",
    285: "ctrl_r",
    42: "shift_l",
    54: "shift_r",
    56: "alt_l",
    312: "alt_r",
}


def _mod_from_native_vk(vk: int) -> str | None:
    return _WIN_VK_TO_MOD.get(vk)


def _mod_from_native_scan(scan: int) -> str | None:
    return _WIN_SCAN_TO_MOD.get(scan)


def _query_held_modifiers_win32() -> list[str]:
    import ctypes

    user32 = ctypes.windll.user32
    held = []
    for vk, name in _WIN_VK_TO_MOD.items():
        if user32.GetAsyncKeyState(vk) & 0x8000:
            held.append(name)
    return held


class KeyBindDialog(QDialog):
    """捕获键盘按键用于绑定，支持组合键与左右修饰键"""

    key_bound = pyqtSignal(int, str)

    def __init__(self, button_index: int, parent=None):
        super().__init__(parent)
        self._button_index = button_index
        self._captured_key: str | None = None
        self._pending_modifier: str | None = None
        self._capturing = False
        self._setup_ui()

    def _set_capturing(self, on: bool) -> None:
        """进入捕获模式时把焦点从搜索框/树上收回来"""
        self._capturing = on
        if on:
            self._tree.clearSelection()
            self.setFocus()
            self._key_label.setText("按下你想绑定的键…")
        else:
            self._key_label.setText("未选择")

    def _setup_ui(self):
        self.setWindowTitle("绑定键盘键")
        self.setFixedSize(640, 760)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 28)

        title = QLabel("按键绑定")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        btn_name = SLOTS[self._button_index].name
        hint = QLabel(
            f"为「{btn_name}」选择动作\n"
            "从列表里挑，或用「直接按键捕获」按下实际按键（支持组合键）\n"
            "Win+Tab 等系统快捷键 Windows 会拦截实时捕获，请从列表选\n"
            "（Esc 取消）"
        )
        hint.setObjectName("dialogHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索动作，如 复制 / ctrl / F5 / 滚轮")
        self._search.setObjectName("searchBox")
        self._search.textChanged.connect(self._filter_tree)
        layout.addWidget(self._search)

        self._tree = QTreeWidget()
        self._tree.setObjectName("catalogTree")
        self._tree.setHeaderHidden(True)
        self._tree.setMinimumHeight(240)
        self._build_tree()
        self._tree.itemSelectionChanged.connect(self._on_tree_selection)
        layout.addWidget(self._tree, stretch=1)

        # 实时捕获与浏览列表必须显式切换：两者都要键盘焦点，同时开着会打架
        self._capture_btn = QPushButton("⌨  直接按键捕获")
        self._capture_btn.setObjectName("refreshBtn")
        self._capture_btn.setCheckable(True)
        self._capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._capture_btn.toggled.connect(self._set_capturing)
        layout.addWidget(self._capture_btn)

        self._key_label = QLabel("未选择")
        self._key_label.setObjectName("keyDisplay")
        self._key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._key_label, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("dialogBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._confirm_btn = QPushButton("确认")
        self._confirm_btn.setObjectName("dialogBtnPrimary")
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(self._confirm_btn)

        layout.addLayout(btn_row)

    def _build_tree(self) -> None:
        for 分类, 项 in CATALOG:
            父 = QTreeWidgetItem(self._tree, [分类])
            父.setFlags(Qt.ItemFlag.ItemIsEnabled)      # 分类本身不可选中
            for 显示名, 值 in 项:
                子 = QTreeWidgetItem(父, [显示名])
                子.setData(0, Qt.ItemDataRole.UserRole, 值)
        self._tree.expandItem(self._tree.topLevelItem(0))

    def _filter_tree(self, 关键词: str) -> None:
        词 = 关键词.strip().lower()
        for i in range(self._tree.topLevelItemCount()):
            父 = self._tree.topLevelItem(i)
            命中数 = 0
            for j in range(父.childCount()):
                子 = 父.child(j)
                值 = 子.data(0, Qt.ItemDataRole.UserRole) or ""
                命中 = not 词 or 词 in 子.text(0).lower() or 词 in 值.lower()
                子.setHidden(not 命中)
                命中数 += int(命中)
            父.setHidden(命中数 == 0)
            if 词:
                父.setExpanded(命中数 > 0)

    def _on_tree_selection(self) -> None:
        项 = self._tree.selectedItems()
        if not 项:
            return
        值 = 项[0].data(0, Qt.ItemDataRole.UserRole)
        if 值:
            self._apply_preset(值)

    def _display_for(self, 值: str) -> str:
        """哨兵动作显示中文名 —— 别把 @mouse:left 摆给用户看"""
        if 值 in MOUSE_ACTIONS:
            for _, 项 in CATALOG:
                for 显示名, v in 项:
                    if v == 值:
                        return 显示名
        return self._format_display(值)

    def _apply_preset(self, combo: str) -> None:
        self._captured_key = combo
        self._key_label.setText(self._display_for(combo))
        self._confirm_btn.setEnabled(True)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return

        # 未进入捕获模式时不抢键盘 —— 否则在搜索框里打字会被当成要绑的键
        if not self._capturing:
            super().keyPressEvent(event)
            return

        if event.key() in _MODIFIER_KEYS:
            self._pending_modifier = self._modifier_from_event(event)
            mods = self._active_modifiers(event)
            if mods:
                preview = " + ".join(self._format_display(m) for m in mods) + " + …"
                self._key_label.setText(preview)
            elif self._pending_modifier:
                self._key_label.setText(self._format_display(self._pending_modifier) + " + …")
            self._confirm_btn.setEnabled(False)
            return

        combo = self._event_to_combo(event)
        if combo:
            self._captured_key = combo
            self._key_label.setText(self._format_display(combo))
            self._confirm_btn.setEnabled(True)

    def keyReleaseEvent(self, event: QKeyEvent):
        if not self._capturing:
            super().keyReleaseEvent(event)
            return
        if self._captured_key:
            return

        if event.key() not in _MODIFIER_KEYS and event.key() not in (
            Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R
        ):
            return

        mod = self._pending_modifier or self._modifier_from_event(event)
        if not mod and event.key() in (Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R):
            mod = "cmd"
        if not mod:
            return

        self._captured_key = mod
        self._key_label.setText(self._format_display(mod))
        self._confirm_btn.setEnabled(True)
        self._pending_modifier = None

    def _modifier_from_event(self, event: QKeyEvent) -> str | None:
        win_keys = (Qt.Key.Key_Meta, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R)
        if event.key() not in _MODIFIER_KEYS and event.key() not in win_keys:
            return None

        if sys.platform == "win32":
            held = _query_held_modifiers_win32()
            if len(held) == 1:
                return held[0]
            if len(held) > 1:
                for probe in (
                    _mod_from_native_vk(event.nativeVirtualKey()),
                    _mod_from_native_scan(event.nativeScanCode()),
                ):
                    if probe and probe in held:
                        return probe

            if event.key() == Qt.Key.Key_Super_R:
                return "cmd_r"
            if event.key() in (Qt.Key.Key_Meta, Qt.Key.Key_Super_L):
                return "cmd_l"

            scan_mod = _mod_from_native_scan(event.nativeScanCode())
            if scan_mod:
                return scan_mod

        vk = event.nativeVirtualKey()
        specific = _mod_from_native_vk(vk)
        if specific:
            return specific
        if event.key() in win_keys:
            return "cmd"
        return _MODIFIER_KEYS.get(event.key())

    def _active_modifiers(self, event: QKeyEvent | None = None) -> list[str]:
        if sys.platform == "win32":
            held = _query_held_modifiers_win32()
            if held:
                return [m for m in _MODIFIER_ORDER if m in held]

        if event is None:
            return []

        mods = event.modifiers()
        result = []
        if mods & Qt.KeyboardModifier.MetaModifier:
            if sys.platform == "win32":
                held = _query_held_modifiers_win32()
                win_mods = [m for m in ("cmd_l", "cmd_r") if m in held]
                if win_mods:
                    result.extend(win_mods)
                else:
                    result.append("cmd")
            else:
                result.append("cmd")
        if mods & Qt.KeyboardModifier.ControlModifier:
            result.append("ctrl")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            result.append("shift")
        if mods & Qt.KeyboardModifier.AltModifier:
            result.append("alt")
        return result

    def _resolve_main_key(self, event: QKeyEvent) -> str | None:
        key = event.key()
        if key in _QT_KEY_MAP:
            return _QT_KEY_MAP[key]
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(key).lower()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return chr(key)
        text = event.text()
        if text and text.isprintable() and len(text) == 1:
            return text
        return None

    def _symbol_from_event(self, event: QKeyEvent) -> str | None:
        """Shift+9 等得到 ( ) [ ] { } 时，绑定该符号本身，而不是 shift+数字。"""
        text = event.text()
        if not text or len(text) != 1 or not text.isprintable():
            return None
        if text.isalnum() or text.isspace():
            return None
        mods = self._active_modifiers(event)
        if any(m.startswith("ctrl") or m.startswith("alt") for m in mods):
            return None
        return text

    def _event_to_combo(self, event: QKeyEvent) -> str | None:
        symbol = self._symbol_from_event(event)
        if symbol:
            return symbol

        main = self._resolve_main_key(event)
        if not main:
            return None

        mods = self._active_modifiers(event)
        parts = [m for m in _MODIFIER_ORDER if m in mods]
        # 输出统一用 cmd，pynput 在 Windows 上更稳定
        parts = ["cmd" if p in ("cmd_l", "cmd_r", "win", "super") else p for p in parts]
        seen: set[str] = set()
        deduped: list[str] = []
        for part in parts:
            if part not in seen:
                seen.add(part)
                deduped.append(part)
        parts = deduped
        parts.append(main)
        return "+".join(parts)

    @classmethod
    def _format_display(cls, combo: str) -> str:
        def fmt(part: str) -> str:
            if part in _DISPLAY_NAMES:
                return _DISPLAY_NAMES[part]
            if part in ("cmd", "win", "super", "cmd_l", "cmd_r"):
                return "Win"
            return part.upper() if len(part) == 1 else part

        return " + ".join(fmt(part) for part in combo.split("+"))

    def _confirm(self):
        if self._captured_key:
            self.key_bound.emit(self._button_index, self._captured_key)
            self.accept()
