# -*- coding: utf-8 -*-
"""可绑定动作的分类目录

纯数据，不依赖 Qt —— 绑定对话框据此构建分类列表。

**这里列出的每一项，引擎都必须真的发得出去**：鼠标类只能是
mapping_engine 认识的哨兵动作，键盘类每个部件都要能被
KeyboardOutput._resolve_key 解析。tests/test_key_catalog.py 守这条。
"""

from core.constants import (
    MOUSE_LEFT,
    MOUSE_MIDDLE,
    MOUSE_RIGHT,
    WHEEL_DOWN,
    WHEEL_UP,
)

# (分类名, ((显示名, 绑定值), ...))
CATALOG = (
    ("鼠标", (
        ("鼠标左键", MOUSE_LEFT),
        ("鼠标右键", MOUSE_RIGHT),
        ("鼠标中键", MOUSE_MIDDLE),
        ("滚轮上滚", WHEEL_UP),
        ("滚轮下滚", WHEEL_DOWN),
    )),
    ("Windows 快捷键", (
        ("任务视图  Win+Tab", "cmd+tab"),
        ("显示桌面  Win+D", "cmd+d"),
        ("资源管理器  Win+E", "cmd+e"),
        ("锁定屏幕  Win+L", "cmd+l"),
        ("运行  Win+R", "cmd+r"),
        ("截图  Win+Shift+S", "cmd+shift+s"),
        ("设置  Win+I", "cmd+i"),
        ("切换窗口  Alt+Tab", "alt+tab"),
        ("关闭窗口  Alt+F4", "alt+f4"),
        ("任务管理器  Ctrl+Shift+Esc", "ctrl+shift+esc"),
    )),
    ("编辑", (
        ("复制  Ctrl+C", "ctrl+c"),
        ("粘贴  Ctrl+V", "ctrl+v"),
        ("剪切  Ctrl+X", "ctrl+x"),
        ("撤销  Ctrl+Z", "ctrl+z"),
        ("重做  Ctrl+Y", "ctrl+y"),
        ("全选  Ctrl+A", "ctrl+a"),
        ("保存  Ctrl+S", "ctrl+s"),
        ("查找  Ctrl+F", "ctrl+f"),
    )),
    ("导航", (
        ("上", "up"), ("下", "down"), ("左", "left"), ("右", "right"),
        ("Home", "home"), ("End", "end"),
        ("上一页  Page Up", "page_up"), ("下一页  Page Down", "page_down"),
        ("Tab", "tab"), ("反向 Tab  Shift+Tab", "shift+tab"),
        ("回车  Enter", "enter"), ("退出  Esc", "escape"),
        ("空格", "space"), ("退格", "backspace"), ("删除", "delete"),
    )),
    ("功能键", tuple((f"F{i}", f"f{i}") for i in range(1, 13))),
    ("字母", tuple((c.upper(), c) for c in "abcdefghijklmnopqrstuvwxyz")),
    ("数字", tuple((str(i), str(i)) for i in range(10))),
    ("修饰键", (
        ("左 Ctrl", "ctrl_l"), ("右 Ctrl", "ctrl_r"),
        ("左 Shift", "shift_l"), ("右 Shift", "shift_r"),
        ("左 Alt", "alt_l"), ("右 Alt", "alt_r"),
        ("Win", "cmd"),
    )),
)

# 鼠标类的绑定值集合，供 UI 与测试区分「这不是键盘键」
MOUSE_ACTIONS = frozenset(值 for _, 项 in CATALOG[:1] for _, 值 in 项)


def all_entries():
    """展平成 (分类, 显示名, 绑定值) 三元组"""
    for 分类, 项 in CATALOG:
        for 显示名, 值 in 项:
            yield 分类, 显示名, 值
