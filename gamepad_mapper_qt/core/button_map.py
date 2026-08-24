# -*- coding: utf-8 -*-
"""硬件按键 → 逻辑槽位映射（Xbox / SDL）"""

from typing import List, Optional

# 逻辑槽位索引（与 BUTTON_NAMES 一致）
IDX_LT = 6
IDX_RT = 7
IDX_BACK = 8
IDX_START = 9
IDX_L3 = 10
IDX_R3 = 11

# SDL Xbox 360 / Xbox One 常见布局
XBOX_HW_TO_LOGICAL = {
    0: 0,   # A
    1: 1,   # B
    2: 2,   # X
    3: 3,   # Y
    4: 4,   # LB
    5: 5,   # RB
    6: IDX_BACK,
    7: IDX_START,
    8: IDX_L3,
    9: IDX_R3,
}


def detect_layout(controller_name: str) -> str:
    """根据手柄名称推断映射布局"""
    name = (controller_name or "").lower()
    if "xbox" in name or "x-input" in name or "xinput" in name:
        return "xbox"
    if "playstation" in name or "dualshock" in name or "dualsense" in name:
        return "direct"
    return "xbox"


def apply_hardware_buttons(
    pressed: List[bool],
    get_button,
    num_buttons: int,
    layout: str = "xbox",
) -> None:
    """将 pygame 物理按钮写入逻辑 pressed 数组"""
    if layout == "xbox":
        for hw in range(min(num_buttons, 10)):
            logical = XBOX_HW_TO_LOGICAL.get(hw)
            if logical is not None:
                pressed[logical] = bool(get_button(hw))
        return

    for bi in range(min(num_buttons, 12)):
        pressed[bi] = bool(get_button(bi))
