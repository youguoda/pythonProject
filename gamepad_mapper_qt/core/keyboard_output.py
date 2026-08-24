# -*- coding: utf-8 -*-
"""键盘输出封装"""

from typing import Set

from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key


class KeyboardOutput:
    """pynput 键盘模拟，支持组合键"""

    def __init__(self):
        self._controller = KeyboardController()
        self._pressed: Set[str] = set()

    @staticmethod
    def _resolve_key(key_name: str):
        attr = key_name.replace("-", "_")
        if hasattr(Key, attr):
            return getattr(Key, attr)
        return key_name

    @staticmethod
    def _parse_combo(key_name: str) -> list[str]:
        return [k.strip() for k in key_name.split("+") if k.strip()]

    def press(self, key_name: str) -> None:
        if key_name in self._pressed:
            return
        try:
            if "+" in key_name:
                for part in self._parse_combo(key_name):
                    self._controller.press(self._resolve_key(part))
            else:
                self._controller.press(self._resolve_key(key_name))
            self._pressed.add(key_name)
        except Exception:
            pass

    def release(self, key_name: str) -> None:
        if key_name not in self._pressed:
            return
        try:
            if "+" in key_name:
                for part in reversed(self._parse_combo(key_name)):
                    self._controller.release(self._resolve_key(part))
            else:
                self._controller.release(self._resolve_key(key_name))
            self._pressed.discard(key_name)
        except Exception:
            pass

    def release_all(self) -> None:
        for key_name in list(self._pressed):
            self.release(key_name)

    @property
    def pressed_keys(self) -> Set[str]:
        return set(self._pressed)
