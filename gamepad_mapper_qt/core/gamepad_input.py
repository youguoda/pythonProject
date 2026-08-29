# -*- coding: utf-8 -*-
"""手柄输入：轮询与边沿判定"""

from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, Mapping, Optional


@dataclass(frozen=True)
class InputFrame:
    """一帧输入状态：既带边沿，也带连续量"""

    just_pressed: frozenset[int] = field(default_factory=frozenset)
    just_released: frozenset[int] = field(default_factory=frozenset)
    just_long_pressed: frozenset[int] = field(default_factory=frozenset)
    just_short_released: frozenset[int] = field(default_factory=frozenset)

    connected: bool = True
    pressed: tuple[bool, ...] = ()
    left_stick: tuple[float, float] = (0.0, 0.0)
    right_stick: tuple[float, float] = (0.0, 0.0)
    lt_value: float = 0.0
    rt_value: float = 0.0


class EdgeDetector:
    """把逐帧的按下集合翻译成边沿

    long_press_after 给某些槽位配上「按住多久算长按」的阈值；
    跨过阈值的那一帧，槽位出现在 just_long_pressed，且只出现一次。
    """

    def __init__(self, long_press_after: Optional[Mapping[int, float]] = None) -> None:
        self._prev: frozenset[int] = frozenset()
        self._long_press_after: Dict[int, float] = dict(long_press_after or {})
        self._pressed_at: Dict[int, float] = {}
        self._long_fired: set[int] = set()

    def feed(self, pressed: Iterable[int], now: float) -> InputFrame:
        current = frozenset(pressed)
        just_pressed = current - self._prev
        just_released = self._prev - current

        for slot in just_pressed:
            self._pressed_at[slot] = now

        # 短按判定必须在清理 _pressed_at / _long_fired 之前做
        just_short_released = set()
        for slot in just_released:
            threshold = self._long_press_after.get(slot)
            since = self._pressed_at.get(slot)
            if (
                threshold is not None
                and since is not None
                and slot not in self._long_fired
                and now - since < threshold
            ):
                just_short_released.add(slot)
            self._pressed_at.pop(slot, None)
            self._long_fired.discard(slot)

        just_long_pressed = set()
        for slot, threshold in self._long_press_after.items():
            if slot not in current or slot in self._long_fired:
                continue
            since = self._pressed_at.get(slot)
            if since is not None and now - since >= threshold:
                just_long_pressed.add(slot)
                self._long_fired.add(slot)

        self._prev = current
        return InputFrame(
            just_pressed=just_pressed,
            just_released=just_released,
            just_long_pressed=frozenset(just_long_pressed),
            just_short_released=frozenset(just_short_released),
        )


class GamepadInput:
    """手柄输入的唯一入口：一次 tick 一次轮询，产出一帧

    这是全应用唯一调用 joystick.poll() 的地方 —— 所有消费者读同一帧，
    不再各自采样、各自维护上一帧状态。
    """

    def __init__(
        self,
        joystick,
        long_press_after: Optional[Mapping[int, float]] = None,
    ) -> None:
        self._joystick = joystick
        self._edges = EdgeDetector(long_press_after)

    def tick(self, now: float) -> InputFrame:
        if not self._joystick.connected:
            frame = self._edges.feed(pressed=(), now=now)
            return replace(frame, connected=False)

        result = self._joystick.poll()
        pressed_slots = {i for i, on in enumerate(result.pressed) if on}
        frame = self._edges.feed(pressed=pressed_slots, now=now)
        return replace(
            frame,
            connected=True,
            pressed=tuple(result.pressed),
            left_stick=result.left_stick,
            right_stick=result.right_stick,
            lt_value=result.lt_value,
            rt_value=result.rt_value,
        )
