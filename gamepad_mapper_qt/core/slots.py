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
    Slot( 0, "A", "#4ecca3", (0.62, 0.55, 0.055), "button", Src("button")),
    Slot( 1, "B", "#e94560", (0.72, 0.45, 0.055), "button", Src("button")),
    Slot( 2, "X", "#4a9eff", (0.52, 0.45, 0.055), "button", Src("button")),
    Slot( 3, "Y", "#ffc107", (0.62, 0.35, 0.055), "button", Src("button")),
    Slot( 4, "LB", "#a78bfa", (0.18, 0.28, 0.045), "button", Src("button")),
    Slot( 5, "RB", "#a78bfa", (0.82, 0.28, 0.045), "button", Src("button")),
    Slot( 6, "LT", "#f97316", (0.28, 0.22, 0.04), "button", Src("trigger", axis=4)),
    Slot( 7, "RT", "#f97316", (0.72, 0.22, 0.04), "button", Src("trigger", axis=5)),
    Slot( 8, "Back", "#94a3b8", (0.38, 0.38, 0.035), "button", Src("button")),
    Slot( 9, "Start", "#94a3b8", (0.5, 0.38, 0.035), "button", Src("button")),
    Slot(10, "L3", "#64748b", (0.22, 0.58, 0.03), "button", Src("button")),
    Slot(11, "R3", "#64748b", (0.72, 0.62, 0.03), "button", Src("button")),
    Slot(12, "D-Pad Up", "#38bdf8", (0.5, 0.72, 0.03), "button", Src("hat", axis=1, sign=+1)),
    Slot(13, "D-Pad Down", "#38bdf8", (0.5, 0.88, 0.03), "button", Src("hat", axis=1, sign=-1)),
    Slot(14, "D-Pad Left", "#38bdf8", (0.38, 0.8, 0.03), "button", Src("hat", axis=0, sign=-1)),
    Slot(15, "D-Pad Right", "#38bdf8", (0.62, 0.8, 0.03), "button", Src("hat", axis=0, sign=+1)),
    Slot(16, "Left Stick Up", "#64748b", (0.22, 0.48, 0.0), "dot", Src("stick", axis=1, sign=-1)),
    Slot(17, "Left Stick Down", "#64748b", (0.22, 0.68, 0.0), "dot", Src("stick", axis=1, sign=+1)),
    Slot(18, "Left Stick Left", "#64748b", (0.12, 0.58, 0.0), "dot", Src("stick", axis=0, sign=-1)),
    Slot(19, "Left Stick Right", "#64748b", (0.32, 0.58, 0.0), "dot", Src("stick", axis=0, sign=+1)),
    Slot(20, "Right Stick Up", "#64748b", (0.72, 0.52, 0.0), "dot", Src("stick", axis=3, sign=-1)),
    Slot(21, "Right Stick Down", "#64748b", (0.72, 0.72, 0.0), "dot", Src("stick", axis=3, sign=+1)),
    Slot(22, "Right Stick Right", "#64748b", (0.82, 0.62, 0.0), "dot", Src("stick", axis=2, sign=+1)),
    Slot(23, "Right Stick Left", "#64748b", (0.62, 0.62, 0.0), "dot", Src("stick", axis=2, sign=-1)),
)
