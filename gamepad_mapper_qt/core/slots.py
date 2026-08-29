# -*- coding: utf-8 -*-
"""槽位表：一条记录描述一个槽位的全部静态属性

索引即槽位号，与 profile JSON 的键、映射表行号、InputFrame.pressed 下标一致。
往中间插入或重排会静默改写磁盘上所有 profile 的含义 —— 只能追加到末尾。

面板坐标（panel / render）本属 UI 关切，放在这里是有意的分层妥协：
把它拆去 ui/ 就等于把一个槽位重新劈成两半，而这正是这张表要消除的。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Src:
    """槽位状态的来源

    button  —— 物理按钮，由 button_map.apply_hardware_buttons 按布局填入
    hat     —— 十字键，axis 0=x 1=y，sign 表示取正向还是负向
    stick   —— 摇杆方向，与 threshold 比较
    trigger —— 扳机，归一化后 > 0.5 算按下
    """

    kind: str
    axis: int = -1
    sign: int = 0


@dataclass(frozen=True)
class Slot:
    index: int
    name: str
    color: str
    panel: tuple[float, float, float]   # 相对宽高的 x, y, 半径
    render: str                          # "button" 带标签圆形 / "dot" 摇杆方向小点
    source: "Src"                        # 这个槽位的状态从手柄的哪里读


SLOTS: tuple[Slot, ...] = (
    Slot( 0, "A", "#4ecca3", (0.72, 0.478, 0.036), "button", Src("button")),
    Slot( 1, "B", "#e94560", (0.792, 0.406, 0.036), "button", Src("button")),
    Slot( 2, "X", "#4a9eff", (0.648, 0.406, 0.036), "button", Src("button")),
    Slot( 3, "Y", "#ffc107", (0.72, 0.334, 0.036), "button", Src("button")),
    Slot( 4, "LB", "#a78bfa", (0.268, 0.196, 0.068), "bumper", Src("button")),
    Slot( 5, "RB", "#a78bfa", (0.732, 0.196, 0.068), "bumper", Src("button")),
    Slot( 6, "LT", "#f97316", (0.258, 0.132, 0.046), "trigger", Src("trigger", axis=4)),
    Slot( 7, "RT", "#f97316", (0.742, 0.132, 0.046), "trigger", Src("trigger", axis=5)),
    Slot( 8, "Back", "#5eead4", (0.448, 0.300, 0.030), "button", Src("button")),
    Slot( 9, "Start", "#5eead4", (0.552, 0.300, 0.030), "button", Src("button")),
    Slot(10, "L3", "#64748b", (0.275, 0.395, 0.07), "stick", Src("button")),
    Slot(11, "R3", "#64748b", (0.625, 0.612, 0.07), "stick", Src("button")),
    Slot(12, "D-Pad Up", "#38bdf8", (0.398, 0.548, 0.028), "dpad", Src("hat", axis=1, sign=+1)),
    Slot(13, "D-Pad Down", "#38bdf8", (0.398, 0.662, 0.028), "dpad", Src("hat", axis=1, sign=-1)),
    Slot(14, "D-Pad Left", "#38bdf8", (0.341, 0.605, 0.028), "dpad", Src("hat", axis=0, sign=-1)),
    Slot(15, "D-Pad Right", "#38bdf8", (0.455, 0.605, 0.028), "dpad", Src("hat", axis=0, sign=+1)),
    Slot(16, "Left Stick Up", "#64748b", (0.275, 0.395, 0.07), "stick_dir", Src("stick", axis=1, sign=-1)),
    Slot(17, "Left Stick Down", "#64748b", (0.275, 0.395, 0.07), "stick_dir", Src("stick", axis=1, sign=+1)),
    Slot(18, "Left Stick Left", "#64748b", (0.275, 0.395, 0.07), "stick_dir", Src("stick", axis=0, sign=-1)),
    Slot(19, "Left Stick Right", "#64748b", (0.275, 0.395, 0.07), "stick_dir", Src("stick", axis=0, sign=+1)),
    Slot(20, "Right Stick Up", "#64748b", (0.625, 0.612, 0.07), "stick_dir", Src("stick", axis=3, sign=-1)),
    Slot(21, "Right Stick Down", "#64748b", (0.625, 0.612, 0.07), "stick_dir", Src("stick", axis=3, sign=+1)),
    Slot(22, "Right Stick Right", "#64748b", (0.625, 0.612, 0.07), "stick_dir", Src("stick", axis=2, sign=+1)),
    Slot(23, "Right Stick Left", "#64748b", (0.625, 0.612, 0.07), "stick_dir", Src("stick", axis=2, sign=-1)),
)


# ---------- 槽位的可绑定性 ----------
# 全部派生自既有定义，不在这里重写一份，否则就成了第三处表达。

from core.button_map import UI_RESERVED          # noqa: E402
from core.constants import UNIVERSAL_MOUSE_MAPPINGS  # noqa: E402

FREE = "free"           # 随便绑
RESERVED = "reserved"   # 不给绑，已被保留行为占用
CONFLICT = "conflict"   # 能绑，但会和别的东西抢


def binding_kind(index: int) -> str:
    """这个槽位能不能绑、绑了有没有代价"""
    if index in UI_RESERVED:
        return RESERVED
    if index in UNIVERSAL_MOUSE_MAPPINGS:
        return CONFLICT          # 默认是鼠标左/右键，绑了就覆盖掉
    if SLOTS[index].render == "stick_dir":
        return CONFLICT          # 摇杆同时在驱动鼠标移动/滚轮
    return FREE


def conflict_reason(index: int) -> str:
    """给 UI 显示的一句话说明；FREE 返回空串"""
    kind = binding_kind(index)
    if kind == RESERVED:
        return {
            6: "LT 已用于：短按聚焦窗口、长按切换方案",
            7: "RT 已用于：按住说话（右 Ctrl）",
            9: "Start 已用于：启动/停止映射",
        }.get(index, "已被保留行为占用")
    if kind == CONFLICT:
        if index in UNIVERSAL_MOUSE_MAPPINGS:
            return "默认是统一鼠标层的按键，绑定会覆盖它"
        return "这根摇杆同时在驱动鼠标，绑方向键会互相抢"
    return ""


# ---------- 命中检测 ----------
# 纯几何，不依赖 Qt —— 点在哪，命中哪个槽位。

import math                                       # noqa: E402
from typing import Optional, Tuple                # noqa: E402

FRAME_RATIO = 1.42        # 画框宽高比；坐标全部按画框宽度归一化
_WEDGE_INNER = 1.14       # 摇杆方向扇形的内外半径倍率与张角，
_WEDGE_OUTER = 1.58       # 必须与 gamepad_panel 的绘制常量一致
_WEDGE_SPAN = 64
_DIR_ANGLE = {"Up": 90, "Down": 270, "Left": 180, "Right": 0}


def frame_rect(width: float, height: float) -> Tuple[float, float, float]:
    """返回 (原点x, 原点y, 画框宽)。画框保持固定宽高比并居中。"""
    aw, ah = width * 0.96, height * 0.96   # 与绘制侧的边距一致
    if aw / ah > FRAME_RATIO:
        fw = ah * FRAME_RATIO
    else:
        fw = aw
    fh = fw / FRAME_RATIO
    return (width - fw) / 2, (height - fh) / 2, fw


def _in_rect(dx, dy, half_w, half_h) -> bool:
    return abs(dx) <= half_w and abs(dy) <= half_h


def _in_wedge(dx, dy, r, direction: str) -> bool:
    dist = math.hypot(dx, dy)
    if not (r * _WEDGE_INNER <= dist <= r * _WEDGE_OUTER):
        return False
    # 屏幕坐标 y 向下，取负还原成数学方向；0°=右，90°=上
    angle = math.degrees(math.atan2(-dy, dx)) % 360
    delta = (angle - _DIR_ANGLE[direction] + 180) % 360 - 180
    return abs(delta) <= _WEDGE_SPAN / 2


def hit_test(x: float, y: float, width: float, height: float) -> Optional[int]:
    """点击落在哪个槽位上；没命中返回 None

    先测扇形再测圆盘：扇形在圆盘外环，两者不重叠，但顺序固定便于推理。
    """
    ox, oy, fw = frame_rect(width, height)
    px, py = x - ox, y - oy

    for slot in SLOTS:
        sx, sy, sr = slot.panel
        cx, cy, r = fw * sx, fw * sy, fw * sr
        dx, dy = px - cx, py - cy

        if slot.render == "stick_dir":
            if _in_wedge(dx, dy, r, slot.name.split()[-1]):
                return slot.index
        elif slot.render in ("button", "stick"):
            if math.hypot(dx, dy) <= r:
                return slot.index
        elif slot.render == "bumper":
            if _in_rect(dx, dy, r, r * 0.34):
                return slot.index
        elif slot.render == "trigger":
            if _in_rect(dx, dy, r * 0.72, r * 0.62):
                return slot.index
        elif slot.render == "dpad":
            if _in_rect(dx, dy, r * 0.92, r * 0.92):
                return slot.index
    return None
