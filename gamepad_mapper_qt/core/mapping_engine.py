# -*- coding: utf-8 -*-
"""映射引擎 — 消费输入帧，产生键盘/鼠标输出（闸门 / 语音 / 鼠标）"""

from typing import Callable, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from core.button_map import IDX_LT, IDX_RT
from core.constants import (
    MOUSE_LEFT,
    MOUSE_RIGHT,
    VOICE_KEY,
)
from core.gamepad_input import InputFrame
from core.keyboard_output import KeyboardOutput
from core.mouse_output import MouseOutput

# 引擎不处理的保留槽位：LT 归 MainWindow（聚焦/切方案），RT 恒为语音键
_保留槽位 = (IDX_LT, IDX_RT)


class MappingEngine(QObject):
    """把 InputFrame 翻译成键盘与鼠标输出

    不再自己轮询，也不再是线程 —— 由主循环每帧调用 consume()。
    """

    state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    gate_changed = pyqtSignal(bool, str)

    def __init__(
        self,
        keyboard: KeyboardOutput,
        mouse: MouseOutput,
        parent=None,
    ):
        super().__init__(parent)
        self._keyboard = keyboard
        self._mouse = mouse
        self._mappings: Dict[int, str] = {}
        self._active = False
        self._gate_checker: Optional[Callable[[], bool]] = None
        self._process_names: list[str] = []
        self._mouse_sensitivity = 12.0
        self._stick_deadzone = 0.15
        self._scroll_sensitivity = 1.0
        self._rt_voice_held = False
        self._last_gate_open = True
        self._last_gate_label = ""
        self._已报错的动作: set[str] = set()

    def set_mappings(self, mappings: Dict[int, str]) -> None:
        self._mappings = dict(mappings)
        # 改了绑定就重新给每个动作一次上报机会
        self._已报错的动作.clear()

    def set_gate_checker(self, checker: Optional[Callable[[], bool]]) -> None:
        self._gate_checker = checker

    def set_process_names(self, names: list[str]) -> None:
        self._process_names = list(names)

    def set_mouse_settings(
        self,
        sensitivity: float,
        deadzone: float,
        scroll_sensitivity: float,
    ) -> None:
        self._mouse_sensitivity = sensitivity
        self._stick_deadzone = deadzone
        self._scroll_sensitivity = scroll_sensitivity

    def start_mapping(self) -> None:
        if self._active:
            return
        self._active = True
        self._rt_voice_held = False
        self.state_changed.emit(True)

    def stop_mapping(self) -> None:
        self._active = False
        self._release_all_output()
        self.state_changed.emit(False)

    @property
    def is_active(self) -> bool:
        return self._active

    def _is_gate_open(self) -> bool:
        if self._gate_checker:
            return self._gate_checker()
        return True

    def _emit_gate_state(self, open_: bool) -> None:
        label = ", ".join(self._process_names[:2]) if self._process_names else "任意"
        if open_ != self._last_gate_open or label != self._last_gate_label:
            self._last_gate_open = open_
            self._last_gate_label = label
            self.gate_changed.emit(open_, label)

    def _release_rt_voice(self) -> None:
        if self._rt_voice_held:
            self._keyboard.release(VOICE_KEY)
            self._rt_voice_held = False

    def _release_all_output(self) -> None:
        self._release_rt_voice()
        self._keyboard.release_all()
        self._mouse.left_up()
        self._mouse.right_up()

    def consume(self, frame: InputFrame) -> None:
        """处理一帧输入。由主循环调用，不自己计时。"""
        if not self._active or not frame.connected:
            return

        try:
            self._consume(frame)
        except Exception as exc:
            self.error_occurred.emit(str(exc))

    def _consume(self, frame: InputFrame) -> None:
        gate_open = self._is_gate_open()
        self._emit_gate_state(gate_open)

        if not gate_open:
            self._release_all_output()
            return

        # 逐槽位捕获：一个键发不出去，不该让同一帧的其他键跟着失效
        for slot in frame.just_pressed:
            self._试(slot, self._按下)
        for slot in frame.just_released:
            self._试(slot, self._松开)

        self._处理语音(frame.rt_value)
        self._处理鼠标(frame)

    def _试(self, slot: int, 动作) -> None:
        try:
            动作(slot)
        except Exception as exc:
            self._报告失败(self._mappings.get(slot, f"槽位 {slot}"), exc)

    def _报告失败(self, action: str, exc: Exception) -> None:
        """同一个动作只上报一次，否则按住无效键会 60Hz 刷屏"""
        if action in self._已报错的动作:
            return
        self._已报错的动作.add(action)
        self.error_occurred.emit(f"按键「{action}」发送失败: {exc}")

    def _按下(self, slot: int) -> None:
        if slot in _保留槽位:
            return
        action = self._mappings.get(slot)
        if not action:
            return
        if action == MOUSE_LEFT:
            self._mouse.left_down()
        elif action == MOUSE_RIGHT:
            self._mouse.right_down()
        else:
            self._keyboard.press(action)

    def _松开(self, slot: int) -> None:
        if slot in _保留槽位:
            return
        action = self._mappings.get(slot)
        if not action:
            return
        if action == MOUSE_LEFT:
            self._mouse.left_up()
        elif action == MOUSE_RIGHT:
            self._mouse.right_up()
        else:
            self._keyboard.release(action)

    def _处理语音(self, rt_value: float) -> None:
        rt_pressed = rt_value > 0.5
        if rt_pressed and not self._rt_voice_held:
            self._keyboard.press(VOICE_KEY)
            self._rt_voice_held = True
        elif not rt_pressed and self._rt_voice_held:
            self._keyboard.release(VOICE_KEY)
            self._rt_voice_held = False

    def _处理鼠标(self, frame: InputFrame) -> None:
        dz = self._stick_deadzone

        lx, ly = frame.left_stick
        if abs(lx) > dz or abs(ly) > dz:
            self._mouse.move(lx, ly, self._mouse_sensitivity)

        _, ry = frame.right_stick
        if ry < -dz:
            self._mouse.wheel(self._scroll_sensitivity)
        elif ry > dz:
            self._mouse.wheel(-self._scroll_sensitivity)

    def terminate_engine(self) -> None:
        self._active = False
        self._release_all_output()
