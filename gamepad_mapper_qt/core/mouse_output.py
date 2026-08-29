# -*- coding: utf-8 -*-
"""鼠标模拟输出（Windows ctypes）"""

import ctypes

MOUSE_MOVE = 0x0001
MOUSE_LEFT_DOWN = 0x0002
MOUSE_LEFT_UP = 0x0004
MOUSE_RIGHT_DOWN = 0x0008
MOUSE_RIGHT_UP = 0x0010
MOUSE_WHEEL = 0x0800


class MouseOutput:
    """相对移动、点击、滚轮"""

    def __init__(self):
        self._user32 = ctypes.windll.user32

    def move(self, dx: float, dy: float, sensitivity: float = 1.0) -> None:
        final_dx = int(dx * sensitivity)
        final_dy = int(dy * sensitivity)
        if final_dx or final_dy:
            self._user32.mouse_event(MOUSE_MOVE, final_dx, final_dy, 0, 0)

    def left_down(self) -> None:
        self._user32.mouse_event(MOUSE_LEFT_DOWN, 0, 0, 0, 0)

    def left_up(self) -> None:
        self._user32.mouse_event(MOUSE_LEFT_UP, 0, 0, 0, 0)

    def right_down(self) -> None:
        self._user32.mouse_event(MOUSE_RIGHT_DOWN, 0, 0, 0, 0)

    def right_up(self) -> None:
        self._user32.mouse_event(MOUSE_RIGHT_UP, 0, 0, 0, 0)

    def wheel(self, delta: float) -> None:
        if delta:
            self._user32.mouse_event(MOUSE_WHEEL, 0, 0, int(delta * 120), 0)
