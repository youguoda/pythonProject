# -*- coding: utf-8 -*-
"""键盘输出封装"""

from typing import Set

from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key


class KeyboardOutput:
    """pynput 键盘模拟，支持组合键"""

    def __init__(self, controller=None):
        # 生产用 pynput，测试注入假控制器
        self._controller = controller if controller is not None else KeyboardController()
        self._pressed: Set[str] = set()

    @staticmethod
    def _resolve_key(key_name: str):
        aliases = {
            "pageup": "page_up",
            "pagedown": "page_down",
            "win": "cmd",
            "super": "cmd",
            "windows": "cmd",
            "cmd_l": "cmd",
        }
        attr = aliases.get(key_name, key_name.replace("-", "_"))
        if hasattr(Key, attr):
            return getattr(Key, attr)
        return key_name

    @staticmethod
    def _parse_combo(key_name: str) -> list[str]:
        if key_name in ("+", "[", "]", "(", ")"):
            return [key_name]
        return [k.strip() for k in key_name.split("+") if k.strip()]

    def press(self, key_name: str) -> None:
        """按下一个键或组合键。

        失败时向上抛，不静默吞 —— 由调用方决定怎么上报。
        组合键按到一半失败会回滚已按下的部分，否则修饰键会卡在按下状态。
        """
        if key_name in self._pressed:
            return

        if "+" in key_name and key_name not in ("+",):
            pressed_parts: list[str] = []
            try:
                for part in self._parse_combo(key_name):
                    self._controller.press(self._resolve_key(part))
                    pressed_parts.append(part)
            except Exception:
                for part in reversed(pressed_parts):
                    try:
                        self._controller.release(self._resolve_key(part))
                    except Exception:
                        pass
                raise
        else:
            self._controller.press(self._resolve_key(key_name))

        self._pressed.add(key_name)

    def release(self, key_name: str) -> None:
        """松开一个键或组合键。

        与 press 对称：失败向上抛，由调用方决定怎么上报。
        但组合键中途失败时**继续松开剩下的部分**再抛 —— 这里和 press 相反，
        press 要回滚已按下的，release 要尽力把能松的都松开，否则修饰键卡住。
        无论成败都从已按下集合移除：留着它只会让 release_all 反复失败。
        """
        if key_name not in self._pressed:
            return

        self._pressed.discard(key_name)
        first_error = None

        if "+" in key_name and key_name not in ("+",):
            for part in reversed(self._parse_combo(key_name)):
                try:
                    self._controller.release(self._resolve_key(part))
                except Exception as exc:
                    first_error = first_error or exc
        else:
            self._controller.release(self._resolve_key(key_name))

        if first_error is not None:
            raise first_error

    def release_all(self) -> None:
        """尽力松开全部；单个键失败不影响其余，最后抛第一个错误"""
        first_error = None
        for key_name in list(self._pressed):
            try:
                self.release(key_name)
            except Exception as exc:
                first_error = first_error or exc
        if first_error is not None:
            raise first_error

    @property
    def pressed_keys(self) -> Set[str]:
        return set(self._pressed)
