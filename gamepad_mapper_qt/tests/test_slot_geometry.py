# -*- coding: utf-8 -*-
"""槽位几何与可绑定性规格

命中检测是纯几何，不需要 Qt 也不需要手柄。
「点得准不准」是肉眼最难发现的错误，所以这里测得细一点。
"""

import math

import pytest

from core.slots import (
    CONFLICT,
    FREE,
    RESERVED,
    SLOTS,
    binding_kind,
    conflict_reason,
    frame_rect,
    hit_test,
)

宽, 高 = 660, 470


def 槽位中心(index):
    ox, oy, fw = frame_rect(宽, 高)
    sx, sy, _ = SLOTS[index].panel
    return ox + fw * sx, oy + fw * sy


def 扇形中点(index):
    """摇杆方向的热区在圆盘外环，中心点要沿方向外推"""
    ox, oy, fw = frame_rect(宽, 高)
    sx, sy, sr = SLOTS[index].panel
    角 = math.radians({"Up": 90, "Down": 270, "Left": 180, "Right": 0}[
        SLOTS[index].name.split()[-1]])
    d = fw * sr * 1.3
    return ox + fw * sx + d * math.cos(角), oy + fw * sy - d * math.sin(角)


# ---------- 命中检测 ----------

@pytest.mark.parametrize("index", [s.index for s in SLOTS if s.render != "stick_dir"])
def test_每个槽位的中心命中自己(index):
    x, y = 槽位中心(index)
    assert hit_test(x, y, 宽, 高) == index


@pytest.mark.parametrize("index", [s.index for s in SLOTS if s.render == "stick_dir"])
def test_摇杆方向扇形命中自己(index):
    x, y = 扇形中点(index)
    assert hit_test(x, y, 宽, 高) == index


def test_摇杆圆盘中心命中的是_L3_而不是方向():
    """圆盘和四周扇形不能重叠，否则点摇杆永远绑不到 L3"""
    x, y = 槽位中心(10)
    assert hit_test(x, y, 宽, 高) == 10


def test_空白处不命中():
    assert hit_test(3, 3, 宽, 高) is None
    assert hit_test(宽 - 3, 高 - 3, 宽, 高) is None


def test_窗口拉伸后命中依然正确():
    """画框保持宽高比居中，坐标随之平移 —— 拉扁拉长都不该错位"""
    for w, h in [(900, 400), (500, 700), (1200, 845)]:
        ox, oy, fw = frame_rect(w, h)
        for index in (0, 3, 10, 15):
            sx, sy, _ = SLOTS[index].panel
            x, y = ox + fw * sx, oy + fw * sy
            assert hit_test(x, y, w, h) == index, f"{w}x{h} 槽位{index}"


# ---------- 可绑定性 ----------

def test_保留槽位不可绑定():
    for index in (6, 7, 9):          # LT / RT / Start
        assert binding_kind(index) == RESERVED
        assert conflict_reason(index) != ""


def test_统一鼠标层槽位标为冲突():
    for index in (10, 11):           # L3 / R3
        assert binding_kind(index) == CONFLICT


def test_摇杆方向标为冲突():
    for slot in SLOTS:
        if slot.render == "stick_dir":
            assert binding_kind(slot.index) == CONFLICT


def test_可自由绑定的正好是那十一个():
    """与所有 profile 实际绑定的槽位一致 —— 模型没有脱离真实用法"""
    自由 = [s.index for s in SLOTS if binding_kind(s.index) == FREE]
    assert 自由 == [0, 1, 2, 3, 4, 5, 8, 12, 13, 14, 15]
