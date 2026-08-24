# -*- coding: utf-8 -*-
"""按键绑定弹窗 — 支持组合键与左右修饰键捕获"""

import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from core.constants import BUTTON_NAMES


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
}

# Windows virtual-key codes for left/right modifiers
_WIN_VK_TO_MOD = {
    0xA2: "ctrl_l",
    0xA3: "ctrl_r",
    0xA0: "shift_l",
    0xA1: "shift_r",
    0xA4: "alt_l",
    0xA5: "alt_r",
}

_MODIFIER_ORDER = (
    "ctrl_l", "ctrl_r", "ctrl",
    "shift_l", "shift_r", "shift",
    "alt_l", "alt_r", "alt",
)

_DISPLAY_NAMES = {
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


def _mod_from_native_vk(vk: int) -> str | None:
    return _WIN_VK_TO_MOD.get(vk)


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
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("绑定键盘键")
        self.setFixedSize(460, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("[*] 按键绑定")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        btn_name = BUTTON_NAMES[self._button_index]
        hint = QLabel(
            f"为「{btn_name}」绑定键盘键\n"
            "支持组合键，如 Left Ctrl+C、Right Shift+A\n"
            "（Esc 取消；单独绑定修饰键时，按下后松开即可）"
        )
        hint.setObjectName("dialogHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self._key_label = QLabel("等待按键…")
        self._key_label.setObjectName("keyDisplay")
        self._key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._key_label, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._confirm_btn = QPushButton("确认")
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(self._confirm_btn)

        layout.addLayout(btn_row)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return

        if event.key() in _MODIFIER_KEYS:
            mods = self._active_modifiers(event)
            if mods:
                preview = " + ".join(self._format_display(m) for m in mods) + " + …"
                self._key_label.setText(preview)
            self._confirm_btn.setEnabled(False)
            return

        combo = self._event_to_combo(event)
        if combo:
            self._captured_key = combo
            self._key_label.setText(self._format_display(combo))
            self._confirm_btn.setEnabled(True)

    def keyReleaseEvent(self, event: QKeyEvent):
        if self._captured_key:
            return

        if event.key() not in _MODIFIER_KEYS:
            return

        mod = self._modifier_from_event(event)
        if not mod:
            return

        held = self._active_modifiers(event)
        if len(held) == 1 and held[0] == mod:
            self._captured_key = mod
            self._key_label.setText(self._format_display(mod))
            self._confirm_btn.setEnabled(True)

    def _modifier_from_event(self, event: QKeyEvent) -> str | None:
        vk = event.nativeVirtualKey()
        specific = _mod_from_native_vk(vk)
        if specific:
            return specific
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
            return text.lower()
        return None

    def _event_to_combo(self, event: QKeyEvent) -> str | None:
        main = self._resolve_main_key(event)
        if not main:
            return None

        mods = self._active_modifiers(event)
        parts = [m for m in _MODIFIER_ORDER if m in mods]
        parts.append(main)
        return "+".join(parts)

    @classmethod
    def _format_display(cls, combo: str) -> str:
        return " + ".join(
            _DISPLAY_NAMES.get(part, part.upper() if part in _DISPLAY_NAMES.values() else part)
            for part in combo.split("+")
        )

    def _confirm(self):
        if self._captured_key:
            self.key_bound.emit(self._button_index, self._captured_key)
            self.accept()
