# -*- coding: utf-8 -*-
"""KeyboardOutput 的失败处理规格"""

import pytest

from core.keyboard_output import KeyboardOutput


class 会坏的控制器:
    """按到指定键名就抛异常，其余记账"""

    def __init__(self, 坏键):
        self.坏键 = 坏键
        self.按下的 = []

    def press(self, key):
        if key == self.坏键:
            raise ValueError(f"pynput 不认识 {key}")
        self.按下的.append(key)

    def release(self, key):
        if key in self.按下的:
            self.按下的.remove(key)


def test_组合键部分失败时回滚已按下的部分():
    """ctrl+foobar：ctrl 先按下，foobar 抛异常 —— ctrl 不能留在按下状态"""
    控制器 = 会坏的控制器(坏键="foobar")
    kb = KeyboardOutput(controller=控制器)

    with pytest.raises(ValueError):
        kb.press("ctrl+foobar")

    assert 控制器.按下的 == []
    assert kb.pressed_keys == set()
