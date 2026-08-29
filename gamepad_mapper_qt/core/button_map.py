# -*- coding: utf-8 -*-
"""硬件按键 → 逻辑槽位映射（Xbox / SDL）"""

from typing import List, Optional

# 逻辑槽位索引（与 slots.SLOTS 的下标一致）
IDX_LT = 6
IDX_RT = 7
IDX_BACK = 8
IDX_START = 9
IDX_L3 = 10
IDX_R3 = 11

# 引擎在发键时跳过的槽位：LT 归 MainWindow（聚焦/切方案），RT 恒为语音键。
ENGINE_SKIPPED = (IDX_LT, IDX_RT)

# UI 拒绝绑定的槽位 —— 比 ENGINE_SKIPPED 多一个 Start。
# 这个不对称是真实的：引擎并不跳过 Start，所以手改 profile 绑了 Start，
# 按下时会「既发出那个键、又启停映射」。UI 不给绑是为了避免这个隐藏冲突，
# 但它不是引擎层面的保证。
UI_RESERVED = (IDX_LT, IDX_RT, IDX_START)

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
