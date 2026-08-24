# -*- coding: utf-8 -*-
"""手柄检测与轮询"""

import threading
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame

from core.constants import BUTTON_NAMES, DEFAULT_THRESHOLD


@dataclass
class PollResult:
    """一次轮询结果"""

    pressed: List[bool] = field(default_factory=lambda: [False] * len(BUTTON_NAMES))
    left_stick: Tuple[float, float] = (0.0, 0.0)
    right_stick: Tuple[float, float] = (0.0, 0.0)
    lt_value: float = 0.0
    rt_value: float = 0.0


class JoystickManager:
    """单手柄管理器，线程安全"""

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self._lock = threading.RLock()
        self._joystick: Optional[pygame.joystick.JoystickType] = None
        self._name = ""
        self._threshold = threshold
        self._initialized = False

    @property
    def threshold(self) -> float:
        with self._lock:
            return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        with self._lock:
            self._threshold = max(0.1, min(0.95, value))

    @property
    def connected(self) -> bool:
        with self._lock:
            return self._joystick is not None

    @property
    def name(self) -> str:
        with self._lock:
            return self._name

    def ensure_init(self) -> None:
        with self._lock:
            if not self._initialized:
                pygame.init()
                pygame.joystick.init()
                self._initialized = True

    def refresh(self) -> bool:
        """重新检测手柄，返回是否连接成功"""
        with self._lock:
            self.ensure_init()
            self._joystick = None
            self._name = ""

            pygame.joystick.quit()
            pygame.joystick.init()

            if pygame.joystick.get_count() < 1:
                return False

            try:
                js = pygame.joystick.Joystick(0)
                js.init()
                self._joystick = js
                self._name = js.get_name()
                return True
            except pygame.error:
                self._joystick = None
                return False

    def poll(self) -> PollResult:
        """读取当前 24 项按键/方向状态"""
        with self._lock:
            result = PollResult()
            js = self._joystick
            if js is None:
                return result

            pygame.event.pump()
            thr = self._threshold
            pressed = result.pressed

            for bi in range(min(js.get_numbuttons(), 12)):
                pressed[bi] = bool(js.get_button(bi))

            if js.get_numhats() > 0:
                hx, hy = js.get_hat(0)
                pressed[12] = hy > 0
                pressed[13] = hy < 0
                pressed[14] = hx < 0
                pressed[15] = hx > 0

            if js.get_numaxes() >= 2:
                lx, ly = js.get_axis(0), js.get_axis(1)
                result.left_stick = (lx, ly)
                pressed[18] = lx < -thr
                pressed[19] = lx > thr
                pressed[16] = ly < -thr
                pressed[17] = ly > thr

            if js.get_numaxes() >= 4:
                rx, ry = js.get_axis(2), js.get_axis(3)
                result.right_stick = (rx, ry)
                pressed[22] = rx > thr
                pressed[23] = rx < -thr
                pressed[20] = ry < -thr
                pressed[21] = ry > thr

            if js.get_numaxes() >= 6:
                lt = (js.get_axis(4) + 1) / 2
                rt = (js.get_axis(5) + 1) / 2
                result.lt_value = lt
                result.rt_value = rt
                pressed[6] = lt > 0.5
                pressed[7] = rt > 0.5

            return result

    def shutdown(self) -> None:
        with self._lock:
            self._joystick = None
            if self._initialized:
                pygame.joystick.quit()
                pygame.quit()
                self._initialized = False
