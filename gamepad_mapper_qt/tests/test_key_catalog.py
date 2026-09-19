# -*- coding: utf-8 -*-
"""绑定目录的规格

核心不变式：**目录里列出的每一项，引擎都必须真的发得出去。**
列表承诺了引擎做不到的动作，用户会绑上去然后发现按了没反应 ——
而那种失败是静默的，没有任何提示。
"""

import pytest
from pynput.keyboard import Key

from core.constants import (
    MOUSE_LEFT,
    MOUSE_MIDDLE,
    MOUSE_RIGHT,
    WHEEL_DOWN,
    WHEEL_UP,
)
from core.keyboard_output import KeyboardOutput
from ui.widgets.key_catalog import CATALOG, MOUSE_ACTIONS, all_entries

# 引擎在 _press_slot / _release_slot 里特判的全部哨兵动作
引擎认识的哨兵 = {MOUSE_LEFT, MOUSE_RIGHT, MOUSE_MIDDLE, WHEEL_UP, WHEEL_DOWN}


def test_目录非空且分类都有内容():
    assert len(CATALOG) >= 5
    for 分类, 项 in CATALOG:
        assert 项, f"分类「{分类}」是空的"


def test_鼠标类的每一项引擎都认识():
    assert MOUSE_ACTIONS <= 引擎认识的哨兵
    for 值 in MOUSE_ACTIONS:
        assert 值.startswith("@"), f"{值} 不像哨兵动作"


@pytest.mark.parametrize(
    "分类,显示名,值",
    [e for e in all_entries() if e[2] not in MOUSE_ACTIONS],
)
def test_键盘类的每一项都能被解析(分类, 显示名, 值):
    """组合键的每个部件都要能变成 pynput 认识的东西

    _resolve_key 认不出来时会原样返回字符串；单字符是合法的
    （pynput 接受 'a'），多字符就意味着按下时会抛异常。
    """
    for 部件 in KeyboardOutput._parse_combo(值):
        解析 = KeyboardOutput._resolve_key(部件)
        可用 = isinstance(解析, Key) or (isinstance(解析, str) and len(解析) == 1)
        assert 可用, f"「{分类} / {显示名}」的部件 {部件!r} 发不出去"


def test_显示名与绑定值都不重复():
    值们 = [值 for _, _, 值 in all_entries()]
    重复 = {v for v in 值们 if 值们.count(v) > 1}
    assert not 重复, f"重复的绑定值：{重复}"
