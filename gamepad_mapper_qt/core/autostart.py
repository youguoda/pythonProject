# -*- coding: utf-8 -*-
"""Windows 开机自启动（当前用户注册表）"""

import os
import sys

APP_REG_NAME = "GamepadVibeController"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_launch_command() -> str:
    """生成无控制台窗口的启动命令"""
    main_py = os.path.join(_project_root(), "main.py")
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        pythonw = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.isfile(pythonw):
            exe = pythonw
    return f'"{exe}" "{main_py}"'


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
