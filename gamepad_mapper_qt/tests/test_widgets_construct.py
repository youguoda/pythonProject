# -*- coding: utf-8 -*-
"""Widget 构造冒烟测试

只回答一个问题：每个 widget、每个槽位，都能被造出来而不抛异常吗？

存在的理由很具体：候选 4 把 BUTTON_NAMES 换成 SLOTS 时漏给
key_bind_dialog 补 import，点击绑定直接 NameError 崩溃，而当时
72 个测试无一拦住 —— 因为它们全都不碰 ui/。

这是整个套件里唯一依赖 Qt 的文件。
"""

import pytest

from PyQt6.QtWidgets import QApplication

from core.slots import RESERVED, SLOTS, binding_kind


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.mark.parametrize("index", [s.index for s in SLOTS])
def test_每个槽位都能打开绑定对话框(qt_app, index):
    """点手柄图上任何一个键都会走到这里，一个都不能崩"""
    from ui.widgets.key_bind_dialog import KeyBindDialog

    from PyQt6.QtWidgets import QLabel

    dialog = KeyBindDialog(index)
    # 对话框里应当出现该槽位的名字，否则用户不知道在给哪个键绑
    文字 = " ".join(w.text() for w in dialog.findChildren(QLabel))
    assert SLOTS[index].name in 文字
    dialog.close()


def test_映射表能构造并载入映射(qt_app):
    from ui.widgets.mapping_table import MappingTable

    table = MappingTable()
    table.load_mappings({0: "y", 12: "up"})
    assert table.rowCount() == 2          # 默认只列已绑定的
    table.set_show_unbound(True)
    assert table.rowCount() == len(SLOTS) - sum(
        1 for s in SLOTS if binding_kind(s.index) == RESERVED
    )


def test_手柄面板能构造并接收一帧(qt_app):
    from core.gamepad_input import InputFrame
    from ui.widgets.gamepad_panel import GamepadPanel

    panel = GamepadPanel()
    panel.update_state(InputFrame(pressed=tuple([False] * len(SLOTS))))
    panel.set_bindings({0: "y"})
    panel.set_dimmed(True)


def test_状态栏能构造(qt_app):
    from ui.widgets.status_bar import StatusBar

    StatusBar()
