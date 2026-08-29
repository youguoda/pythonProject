# -*- coding: utf-8 -*-
"""EdgeDetector 的行为规格"""

from core.gamepad_input import EdgeDetector


def test_按下只在第一帧算按下边沿():
    det = EdgeDetector()

    第一帧 = det.feed(pressed={0}, now=0.000)
    第二帧 = det.feed(pressed={0}, now=0.016)

    assert 第一帧.just_pressed == {0}
    assert 第二帧.just_pressed == frozenset()


def test_松开只在第一帧算松开边沿():
    det = EdgeDetector()
    det.feed(pressed={0}, now=0.000)

    松开帧 = det.feed(pressed=set(), now=0.016)
    之后 = det.feed(pressed=set(), now=0.032)

    assert 松开帧.just_released == {0}
    assert 之后.just_released == frozenset()


def test_长按跨过阈值只触发一次():
    det = EdgeDetector(long_press_after={6: 0.4})

    det.feed(pressed={6}, now=0.0)
    未到阈值 = det.feed(pressed={6}, now=0.3)
    跨过阈值 = det.feed(pressed={6}, now=0.5)
    继续按住 = det.feed(pressed={6}, now=0.7)

    assert 未到阈值.just_long_pressed == frozenset()
    assert 跨过阈值.just_long_pressed == {6}
    assert 继续按住.just_long_pressed == frozenset()


def test_未到阈值就松开算短按():
    det = EdgeDetector(long_press_after={6: 0.4})

    det.feed(pressed={6}, now=0.0)
    松开帧 = det.feed(pressed=set(), now=0.2)

    assert 松开帧.just_short_released == {6}
    assert 松开帧.just_long_pressed == frozenset()


def test_长按之后松开不算短按():
    det = EdgeDetector(long_press_after={6: 0.4})

    det.feed(pressed={6}, now=0.0)
    跨过阈值 = det.feed(pressed={6}, now=0.5)
    松开帧 = det.feed(pressed=set(), now=0.9)

    assert 跨过阈值.just_long_pressed == {6}
    assert 松开帧.just_short_released == frozenset()


def test_松开后复位可以再次长按():
    det = EdgeDetector(long_press_after={6: 0.4})

    det.feed(pressed={6}, now=0.0)
    det.feed(pressed={6}, now=0.5)      # 第一次长按触发
    det.feed(pressed=set(), now=0.9)    # 松开

    det.feed(pressed={6}, now=1.0)      # 再次按下
    第二次 = det.feed(pressed={6}, now=1.5)

    assert 第二次.just_long_pressed == {6}
