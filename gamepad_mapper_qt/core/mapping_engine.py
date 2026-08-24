# -*- coding: utf-8 -*-
"""映射引擎 — 后台线程"""

import time
from typing import Dict, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core.constants import BUTTON_NAMES
from core.joystick_manager import JoystickManager
from core.keyboard_output import KeyboardOutput


class MappingEngine(QThread):
    """60Hz 映射线程"""

    state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, joystick: JoystickManager, keyboard: KeyboardOutput, parent=None):
        super().__init__(parent)
        self._joystick = joystick
        self._keyboard = keyboard
        self._mappings: Dict[int, str] = {}
        self._active = False
        self._prev_pressed = [False] * len(BUTTON_NAMES)
        self._prev_axis = [0.0] * 6

    def set_mappings(self, mappings: Dict[int, str]) -> None:
        self._mappings = dict(mappings)

    def start_mapping(self) -> None:
        if self._active:
            return
        self._active = True
        self._prev_pressed = [False] * len(BUTTON_NAMES)
        self._prev_axis = [0.0] * 6
        if not self.isRunning():
            self.start()
        self.state_changed.emit(True)

    def stop_mapping(self) -> None:
        self._active = False
        self._keyboard.release_all()
        self.state_changed.emit(False)

    @property
    def is_active(self) -> bool:
        return self._active

    def run(self) -> None:
        while True:
            if not self._active:
                self.msleep(50)
                if not self.isRunning():
                    break
                continue

            try:
                self._tick()
            except Exception as exc:
                self.error_occurred.emit(str(exc))
            self.msleep(16)

    def _tick(self) -> None:
        if not self._joystick.connected:
            return

        result = self._joystick.poll()
        mappings = self._mappings

        for bi, pressed in enumerate(result.pressed):
            if bi in (6, 7):
                continue
            if bi < 12:
                if pressed != self._prev_pressed[bi] and bi in mappings:
                    if pressed:
                        self._keyboard.press(mappings[bi])
                    else:
                        self._keyboard.release(mappings[bi])
                self._prev_pressed[bi] = pressed
            else:
                if bi in mappings:
                    if pressed and not self._prev_pressed[bi]:
                        self._keyboard.press(mappings[bi])
                    elif not pressed and self._prev_pressed[bi]:
                        self._keyboard.release(mappings[bi])
                self._prev_pressed[bi] = pressed

        lt = result.lt_value
        rt = result.rt_value
        prev_lt = (self._prev_axis[4] + 1) / 2
        prev_rt = (self._prev_axis[5] + 1) / 2

        for mi, val, pval in ((6, lt, prev_lt), (7, rt, prev_rt)):
            if mi in mappings:
                if val > 0.5 and pval <= 0.5:
                    self._keyboard.press(mappings[mi])
                elif val <= 0.5 and pval > 0.5:
                    self._keyboard.release(mappings[mi])
            self._prev_pressed[mi] = val > 0.5

        lx, ly = result.left_stick
        rx, ry = result.right_stick
        self._prev_axis[0], self._prev_axis[1] = lx, ly
        self._prev_axis[2], self._prev_axis[3] = rx, ry
        self._prev_axis[4] = lt * 2 - 1
        self._prev_axis[5] = rt * 2 - 1

    def terminate_engine(self) -> None:
        self._active = False
        self._keyboard.release_all()
        self.wait(2000)
