# -*- coding: utf-8 -*-
"""ActiveProfile 的行为规格

它拥有「当前生效的方案」：合并统一鼠标层、落盘时剥离、自动持久化、损坏兜底。
"""

import json

import pytest

from core import config_store as cs
from core.active_profile import ActiveProfile
from core.constants import MOUSE_LEFT, MOUSE_RIGHT


@pytest.fixture
def 配置目录(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "_profiles_dir", lambda: str(tmp_path))
    return tmp_path


def _写方案(目录, pid, **字段):
    数据 = {
        "id": pid,
        "display_name": pid,
        "process_names": [],
        "mappings": {},
        "threshold": 0.5,
        "mouse_sensitivity": 20.0,
        "stick_deadzone": 0.15,
        "scroll_sensitivity": 0.35,
        "universal_mouse": True,
    }
    数据.update(字段)
    (目录 / f"{pid}.json").write_text(
        json.dumps(数据, ensure_ascii=False), encoding="utf-8"
    )


def test_读出来的映射带统一鼠标层(配置目录):
    """磁盘上没写 L3/R3，读出来必须有"""
    _写方案(配置目录, "cursor", mappings={"0": "y"})

    ap = ActiveProfile("cursor")

    assert ap.mappings[0] == "y"
    assert ap.mappings[10] == MOUSE_LEFT
    assert ap.mappings[11] == MOUSE_RIGHT


def test_落盘时剥离统一鼠标层(配置目录):
    """L3/R3 用的是默认值就不写进文件，避免每个方案重复一遍"""
    _写方案(配置目录, "cursor", mappings={"0": "y"})
    ap = ActiveProfile("cursor")

    ap.set_mappings({0: "y", 10: MOUSE_LEFT, 11: MOUSE_RIGHT, 12: "up"})

    落盘 = json.loads((配置目录 / "cursor.json").read_text(encoding="utf-8"))
    写入的映射 = 落盘["mappings"]
    assert "10" not in 写入的映射
    assert "11" not in 写入的映射
    assert 写入的映射 == {"0": "y", "12": "up"}


def test_覆盖统一鼠标层的项会被保留(配置目录):
    """把 L3 改绑成别的键，那就必须写进文件"""
    _写方案(配置目录, "cursor", mappings={})
    ap = ActiveProfile("cursor")

    ap.set_mappings({10: "space"})

    落盘 = json.loads((配置目录 / "cursor.json").read_text(encoding="utf-8"))
    assert 落盘["mappings"]["10"] == "space"


def test_设置后立即可读且往返一致(配置目录):
    _写方案(配置目录, "cursor", mappings={})
    ap = ActiveProfile("cursor")

    ap.set_mappings({0: "y", 12: "up"})

    # 内存里带统一层
    assert ap.mappings[0] == "y"
    assert ap.mappings[10] == MOUSE_LEFT
    # 重新从磁盘读，结果一致
    assert ActiveProfile("cursor").mappings == ap.mappings


# ---------- 损坏兜底 ----------

def test_损坏的方案_setter_不抛且回调一次(配置目录):
    (配置目录 / "cursor.json").write_text('{"mappings": {"0":"y",', encoding="utf-8")
    原始 = (配置目录 / "cursor.json").read_bytes()
    失败 = []

    ap = ActiveProfile("cursor", on_save_failed=失败.append)

    # 每个 setter 都不该抛
    ap.set_mappings({0: "y"})
    ap.set_threshold(0.6)
    ap.set_mouse_sensitivity(30.0)
    ap.set_scroll_sensitivity(0.5)

    assert ap.savable is False
    assert (配置目录 / "cursor.json").read_bytes() == 原始, "损坏文件不许被覆盖"
    assert len(失败) == 1, "同一个原因只上报一次"


def test_正常方案不会触发失败回调(配置目录):
    _写方案(配置目录, "cursor", mappings={})
    失败 = []

    ap = ActiveProfile("cursor", on_save_failed=失败.append)
    ap.set_threshold(0.6)

    assert 失败 == []
    assert ap.savable is True


# ---------- 滑块设置 ----------

def test_滑块设置立即落盘(配置目录):
    _写方案(配置目录, "cursor", mappings={})
    ap = ActiveProfile("cursor")

    ap.set_threshold(0.6)
    ap.set_mouse_sensitivity(30.0)
    ap.set_scroll_sensitivity(0.5)

    落盘 = json.loads((配置目录 / "cursor.json").read_text(encoding="utf-8"))
    assert 落盘["threshold"] == 0.6
    assert 落盘["mouse_sensitivity"] == 30.0
    assert 落盘["scroll_sensitivity"] == 0.5


# ---------- 切换 ----------

def test_切换方案后读到新方案的映射(配置目录):
    _写方案(配置目录, "cursor", mappings={"0": "y"})
    _写方案(配置目录, "browser", mappings={"0": "enter"})
    ap = ActiveProfile("cursor")

    ap.switch_to("browser")

    assert ap.mappings[0] == "enter"
    assert ap.profile.id == "browser"
