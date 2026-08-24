# -*- coding: utf-8 -*-
"""映射引擎 — 后台线程（闸门 / 语音 / 鼠标）"""

from typing import Callable, Dict, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core.constants import (
    BUTTON_NAMES,
    MOUSE_LEFT,
    MOUSE_RIGHT,
    VOICE_KEY,
)
from core.joystick_manager import JoystickManager
from core.keyboard_output import KeyboardOutput
from core.mouse_output import MouseOutput


class MappingEngine(QThread):
    """60Hz 映射线程"""

    state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    gate_changed = pyqtSignal(bool, str)

    def __init__(
        self,
        joystick: JoystickManager,
        keyboard: KeyboardOutput,
        mouse: MouseOutput,
        parent=None,
    ):
        super().__init__(parent)
        self._joystick = joystick
        self._keyboard = keyboard
        self._mouse = mouse
        self._mappings: Dict[int, str] = {}
        self._active = False
        self._prev_pressed = [False] * len(BUTTON_NAMES)
        self._prev_axis = [0.0] * 6
        self._gate_checker: Optional[Callable[[], bool]] = None
        self._process_names: list[str] = []
        self._mouse_sensitivity = 12.0
        self._stick_deadzone = 0.15
        self._scroll_sensitivity = 1.0
        self._rt_voice_held = False
        self._last_gate_open = True
        self._last_gate_label = ""

    def set_mappings(self, mappings: Dict[int, str]) -> None:
        self._mappings = dict(mappings)

    def set_gate_checker(self, checker: Optional[Callable[[], bool]]) -> None:
        self._gate_checker = checker

    def set_process_names(self, names: list[str]) -> None:
        self._process_names = list(names)

    def set_mouse_settings(
        self,
        sensitivity: float,
        deadzone: float,
        scroll_sensitivity: float,
    ) -> None:
        self._mouse_sensitivity = sensitivity
        self._stick_deadzone = deadzone
        self._scroll_sensitivity = scroll_sensitivity

    def start_mapping(self) -> None:
        if self._active:
            return
        self._active = True
        self._prev_pressed = [False] * len(BUTTON_NAMES)
        self._prev_axis = [0.0] * 6
        self._rt_voice_held = False
        if not self.isRunning():
            self.start()
        self.state_changed.emit(True)

    def stop_mapping(self) -> None:
        self._active = False
        self._release_rt_voice()
        self._keyboard.release_all()
        self._mouse.left_up()
        self._mouse.right_up()
        self.state_changed.emit(False)

    @property
    def is_active(self) -> bool:
        return self._active

    def _is_gate_open(self) -> bool:
        if self._gate_checker:
            return self._gate_checker()
        return True

    def _emit_gate_state(self, open_: bool) -> None:
        label = ", ".join(self._process_names[:2]) if self._process_names else "任意"
        if open_ != self._last_gate_open or label != self._last_gate_label:
            self._last_gate_open = open_
            self._last_gate_label = label
            self.gate_changed.emit(open_, label)

    def _release_rt_voice(self) -> None:
        if self._rt_voice_held:
            self._keyboard.release(VOICE_KEY)
            self._rt_voice_held = False

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
        gate_open = self._is_gate_open()
        self._emit_gate_state(gate_open)

        if not gate_open:
            self._release_rt_voice()
            self._keyboard.release_all()
            self._mouse.left_up()
            self._mouse.right_up()
            self._prev_pressed = list(result.pressed)
            lx, ly = result.left_stick
            rx, ry = result.right_stick
            self._prev_axis[0], self._prev_axis[1] = lx, ly
            self._prev_axis[2], self._prev_axis[3] = rx, ry
            self._prev_axis[4] = result.lt_value * 2 - 1
            self._prev_axis[5] = result.rt_value * 2 - 1
            return

        for bi, pressed in enumerate(result.pressed):
            if bi in (6, 7):
                continue
            action = mappings.get(bi)
            if not action:
                self._prev_pressed[bi] = pressed
                continue

            if action == MOUSE_LEFT:
                if pressed != self._prev_pressed[bi]:
                    if pressed:
                        self._mouse.left_down()
                    else:
                        self._mouse.left_up()
                self._prev_pressed[bi] = pressed
                continue

            if action == MOUSE_RIGHT:
                if pressed != self._prev_pressed[bi]:
                    if pressed:
                        self._mouse.right_down()
                    else:
                        self._mouse.right_up()
                self._prev_pressed[bi] = pressed
                continue

            if bi < 12:
                if pressed != self._prev_pressed[bi]:
                    if pressed:
                        self._keyboard.press(action)
                    else:
                        self._keyboard.release(action)
            else:
                if pressed and not self._prev_pressed[bi]:
                    self._keyboard.press(action)
                elif not pressed and self._prev_pressed[bi]:
                    self._keyboard.release(action)
            self._prev_pressed[bi] = pressed

        rt = result.rt_value
        rt_pressed = rt > 0.5
        if rt_pressed and not self._rt_voice_held:
            self._keyboard.press(VOICE_KEY)
            self._rt_voice_held = True
        elif not rt_pressed and self._rt_voice_held:
            self._keyboard.release(VOICE_KEY)
            self._rt_voice_held = False
        self._prev_pressed[7] = rt_pressed

        lx, ly = result.left_stick
        dz = self._stick_deadzone
        if abs(lx) > dz or abs(ly) > dz:
            self._mouse.move(lx, ly, self._mouse_sensitivity)

        _, ry = result.right_stick
        if ry < -dz:
            self._mouse.wheel(self._scroll_sensitivity)
        elif ry > dz:
            self._mouse.wheel(-self._scroll_sensitivity)

        lt = result.lt_value
        self._prev_axis[0], self._prev_axis[1] = lx, ly
        rx, ry = result.right_stick
        self._prev_axis[2], self._prev_axis[3] = rx, ry
        self._prev_axis[4] = lt * 2 - 1
        self._prev_axis[5] = rt * 2 - 1
        self._prev_pressed[6] = lt > 0.5

    def terminate_engine(self) -> None:
        self._active = False
        self._release_rt_voice()
        self._keyboard.release_all()
        self.wait(2000)
