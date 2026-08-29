# -*- coding: utf-8 -*-
"""GamepadInput 的接线规格：轮询结果确实流到 InputFrame"""

from core.gamepad_input import GamepadInput
from core.joystick_manager import PollResult


class 假手柄:
    """只按脚本回放的手柄，不碰 pygame"""

    def __init__(self, *帧):
        self.connected = True
        self._帧 = list(帧)

    def poll(self) -> PollResult:
        return self._帧.pop(0)


def _按下(*槽位, **模拟量) -> PollResult:
    pressed = [False] * 24
    for 槽 in 槽位:
        pressed[槽] = True
    return PollResult(pressed=pressed, **模拟量)


def test_轮询结果流到_frame():
    手柄 = 假手柄(_按下(3, left_stick=(0.5, -0.5), rt_value=0.8))
    输入 = GamepadInput(手柄)

    帧 = 输入.tick(now=0.0)

    assert 帧.just_pressed == {3}
    assert 帧.pressed[3] is True
    assert 帧.left_stick == (0.5, -0.5)
    assert 帧.rt_value == 0.8
