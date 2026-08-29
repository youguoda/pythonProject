# -*- coding: utf-8 -*-
"""手柄检测与轮询"""

import threading
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame

from core.button_map import apply_hardware_buttons, detect_layout
from core.constants import DEFAULT_THRESHOLD
from core.slots import SLOTS


@dataclass
class PollResult:
    """一次轮询结果"""

    pressed: List[bool] = field(default_factory=lambda: [False] * len(SLOTS))
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
        self._layout = "xbox"

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
                self._layout = detect_layout(self._name)
                return True
            except pygame.error:
                self._joystick = None
                return False

    def poll(self) -> PollResult:
        """读取当前 24 项按键/方向状态（Xbox 硬件已校正到逻辑槽）"""
        with self._lock:
            result = PollResult()
            js = self._joystick
            if js is None:
                return result

            pygame.event.pump()
            thr = self._threshold
            pressed = result.pressed

            apply_hardware_buttons(
                pressed,
                js.get_button,
                js.get_numbuttons(),
                self._layout,
            )

            axis_count = js.get_numaxes()
            hat = js.get_hat(0) if js.get_numhats() > 0 else None

            if axis_count >= 2:
                result.left_stick = (js.get_axis(0), js.get_axis(1))
            if axis_count >= 4:
                result.right_stick = (js.get_axis(2), js.get_axis(3))
            if axis_count >= 6:
                result.lt_value = (js.get_axis(4) + 1) / 2
                result.rt_value = (js.get_axis(5) + 1) / 2

            # 槽位从哪来由 SLOTS 声明，这里只按声明取值。
            # 轴成对出现（左摇杆 0/1、右摇杆 2/3、扳机 4/5），
            # 取用某个轴就要求它所在的那一对都存在 —— 与改造前的判断一致。
            for slot in SLOTS:
                src = slot.source
                if src.kind == "button":
                    continue
                if src.kind == "hat":
                    if hat is not None:
                        pressed[slot.index] = hat[src.axis] * src.sign > 0
                    continue
                if axis_count < (src.axis // 2 + 1) * 2:
                    continue
                if src.kind == "stick":
                    pressed[slot.index] = js.get_axis(src.axis) * src.sign > thr
                elif src.kind == "trigger":
                    pressed[slot.index] = (js.get_axis(src.axis) + 1) / 2 > 0.5

            return result

    def shutdown(self) -> None:
        with self._lock:
            self._joystick = None
            if self._initialized:
                pygame.joystick.quit()
                pygame.quit()
                self._initialized = False
