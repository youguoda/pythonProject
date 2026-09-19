# -*- coding: utf-8 -*-
"""Windows 开机自启动（当前用户注册表）"""

import sys

from core import paths

APP_REG_NAME = "GamepadVibeController"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def build_launch_command() -> str:
    """生成开机自启的命令

    打包后是 exe 自己；源码运行时是 pythonw + main.py（避免黑框）。
    两种情况的差别由 paths.launch_target 负责。
    """
    return paths.launch_target()


def is_supported() -> bool:
    return sys.platform == "win32"


def is_enabled() -> bool:
    if not is_supported():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_REG_NAME)
        return True
    except OSError:
        return False


def enable() -> None:
    if not is_supported():
        raise OSError("仅支持 Windows 开机自启动")
    import winreg

    command = build_launch_command()
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, command)


def disable() -> None:
    if not is_supported():
        return
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_REG_NAME)
    except OSError:
        pass


def apply_enabled(enabled: bool) -> None:
    if enabled:
        enable()
    else:
        disable()
