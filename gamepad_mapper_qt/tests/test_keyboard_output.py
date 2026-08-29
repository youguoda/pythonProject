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
        if key == self.坏键:
            raise ValueError(f"pynput 松不开 {key}")
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


def test_组合键松开部分失败时其余仍被松开():
    """release 若中途抛出，已松开的不能回退，剩下的也不该被跳过

    press 会先按住 ctrl 与 a；松开时 a 失败，ctrl 仍必须被松开，
    否则修饰键照样卡住 —— 这正是 press 已经修掉的那类问题。
    """
    控制器 = 会坏的控制器(坏键="__松开时才坏__")
    kb = KeyboardOutput(controller=控制器)
    kb.press("ctrl+a")
    assert len(控制器.按下的) == 2

    控制器.坏键 = "a"          # 让松开 a 失败
    with pytest.raises(ValueError):
        kb.release("ctrl+a")

    from pynput.keyboard import Key
    assert Key.ctrl not in 控制器.按下的, "ctrl 必须已被松开"


def test_松开失败后不再认为该键仍被按住():
    控制器 = 会坏的控制器(坏键="__不坏__")
    kb = KeyboardOutput(controller=控制器)
    kb.press("a")
    控制器.坏键 = "a"

    with pytest.raises(ValueError):
        kb.release("a")

    assert "a" not in kb.pressed_keys, "失败的键不该永远留在已按下集合里"
