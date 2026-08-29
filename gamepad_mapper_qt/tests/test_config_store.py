# -*- coding: utf-8 -*-
"""config_store 的损坏兜底规格

核心不变式：读不了的文件，绝不能被覆盖。
"""

import pytest

from core import config_store as cs


@pytest.fixture
def 配置目录(tmp_path, monkeypatch):
    """把 profiles 目录换成临时目录，不碰真实配置"""
    monkeypatch.setattr(cs, "_profiles_dir", lambda: str(tmp_path))
    return tmp_path


@pytest.fixture
def 状态文件(tmp_path, monkeypatch):
    path = tmp_path / "app_state.json"
    monkeypatch.setattr(cs, "_app_state_path", lambda: str(path))
    return path


完好内容 = """{
  "id": "cursor",
  "display_name": "Cursor",
  "process_names": ["Cursor.exe"],
  "mappings": {"0": "y", "1": "n"},
  "threshold": 0.5,
  "mouse_sensitivity": 20.0,
  "stick_deadzone": 0.15,
  "scroll_sensitivity": 0.35,
  "universal_mouse": true
}"""

# 少一个右花括号
损坏内容 = """{
  "id": "cursor",
  "mappings": {"0": "y", "1": "n"},
  "threshold": 0.5,
"""


def test_损坏的文件读出来标记为不可保存(配置目录):
    (配置目录 / "cursor.json").write_text(损坏内容, encoding="utf-8")

    p = cs.load_profile("cursor")

    assert p is not None, "损坏不该和「不存在」混为一谈"
    assert p.savable is False
    assert p.id == "cursor"


def test_文件不存在返回_None_不是损坏(配置目录):
    assert cs.load_profile("根本没有这个方案") is None


def test_完好的文件正常读且可保存(配置目录):
    (配置目录 / "cursor.json").write_text(完好内容, encoding="utf-8")

    p = cs.load_profile("cursor")

    assert p.savable is True
    assert p.mappings == {0: "y", 1: "n"}
    assert p.process_names == ["Cursor.exe"]


def test_拒绝保存不可保存的_profile(配置目录):
    p = cs.HarnessProfile(id="cursor", display_name="cursor", savable=False)

    with pytest.raises(cs.ConfigNotSavable):
        cs.save_profile(p)


def test_损坏文件在一次加载保存往返后逐字节不变(配置目录):
    """这是这次修复的核心回归测试"""
    文件 = 配置目录 / "cursor.json"
    文件.write_text(损坏内容, encoding="utf-8")
    原始 = 文件.read_bytes()

    p = cs.load_profile("cursor")
    with pytest.raises(cs.ConfigNotSavable):
        cs.save_profile(p)

    assert 文件.read_bytes() == 原始


# ---------- app_state 同样的兜底 ----------

def test_损坏的_app_state_标记为不可保存(状态文件):
    状态文件.write_text('{"active_profile": "cursor",', encoding="utf-8")

    st = cs.load_app_state()

    assert st.savable is False


def test_app_state_不存在时是可保存的默认值(状态文件):
    st = cs.load_app_state()

    assert st.savable is True
    assert st.active_profile == cs.PROFILE_ORDER[0]


def test_损坏的_app_state_不会被覆盖(状态文件):
    状态文件.write_text('{"launch_at_startup": true,', encoding="utf-8")
    原始 = 状态文件.read_bytes()

    st = cs.load_app_state()
    with pytest.raises(cs.ConfigNotSavable):
        cs.save_app_state(st)

    assert 状态文件.read_bytes() == 原始
