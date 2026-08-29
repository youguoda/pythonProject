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


# ---------- 信号接线 ----------
# 构造测试只回答「造得出来吗」，拦不住「一个信号接了两处」。
# 那个 bug 的表现是点一次弹两个对话框、要取消两次。

@pytest.fixture
def 主窗口(qt_app, tmp_path, monkeypatch):
    """配置目录隔离到临时目录 —— ActiveProfile 任何变更立即落盘，
    直接跑在真实 config/ 上会改写用户的方案（已经因此丢过一次数据）。"""
    import shutil
    from core import config_store as cs

    shutil.copytree("config/profiles", tmp_path / "profiles")
    monkeypatch.setattr(cs, "_profiles_dir", lambda: str(tmp_path / "profiles"))
    monkeypatch.setattr(cs, "_app_state_path", lambda: str(tmp_path / "app_state.json"))

    from ui.main_window import MainWindow
    w = MainWindow()
    yield w
    w.close()


def test_点击信号各自只接一处(主窗口):
    """接两处就会弹两个对话框、要取消两次

    直接数接收者，而不是发信号看副作用：直连的 _open_bind_dialog 是在
    connect 时绑定的，事后替换属性拦不住它，测试会真的弹出模态框卡死。
    """
    panel = 主窗口._gamepad_panel
    assert panel.receivers(panel.slot_clicked) == 1
    assert panel.receivers(panel.slot_refused) == 1


def test_保留槽位点击后状态栏说明原因(主窗口):
    上报 = []
    主窗口._status_bar.set_status = lambda text: 上报.append(text)

    主窗口._on_slot_refused(6)      # LT

    assert len(上报) == 1
    assert "LT" in 上报[0]
