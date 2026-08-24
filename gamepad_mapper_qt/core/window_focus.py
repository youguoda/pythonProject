# -*- coding: utf-8 -*-
"""前台窗口检测与聚焦"""

import ctypes
import os
from ctypes import wintypes
from typing import Callable, List, Optional

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def get_foreground_process_name() -> str:
    """返回当前前台窗口进程名（如 Cursor.exe）"""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ""

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ""

    try:
        buf = ctypes.create_unicode_buffer(260)
        size = wintypes.DWORD(260)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value)
    finally:
        kernel32.CloseHandle(handle)
    return ""


def is_process_foreground(process_names: List[str]) -> bool:
    """前台进程是否命中任一进程名（不区分大小写）"""
    if not process_names:
        return True
    current = get_foreground_process_name().lower()
    if not current:
        return False
    targets = {name.lower() for name in process_names}
    return current in targets


def focus_process(process_names: List[str]) -> bool:
    """将第一个匹配进程的主窗口置于前台"""
    if not process_names:
        return False

    targets = {name.lower() for name in process_names}
    found_hwnd: Optional[int] = None

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def enum_proc(hwnd, _lparam):
        nonlocal found_hwnd
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return True

        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return True

        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value
        )
        if not handle:
            return True

        try:
            buf = ctypes.create_unicode_buffer(260)
            size = wintypes.DWORD(260)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                handle, 0, buf, ctypes.byref(size)
            ):
                if os.path.basename(buf.value).lower() in targets:
                    found_hwnd = hwnd
                    return False
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
        return True

    ctypes.windll.user32.EnumWindows(enum_proc, 0)
    if not found_hwnd:
        return False

    user32 = ctypes.windll.user32
    user32.ShowWindow(found_hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(found_hwnd)
    return True
