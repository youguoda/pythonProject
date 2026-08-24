# -*- coding: utf-8 -*-
"""常量定义"""

APP_NAME = "Gamepad Vibe Controller"
APP_VERSION = "2.0.0"
CONFIG_DIR = "config"
CONFIG_FILE = "mapping.json"

PROFILE_ORDER = [
    "cursor", "claude_code", "codex", "zcode", "dsh",
    "browser", "general",
]

# 特殊映射动作（非键盘）
MOUSE_LEFT = "@mouse:left"
MOUSE_RIGHT = "@mouse:right"
VOICE_KEY = "ctrl_r"

# 全方案统一的鼠标层（左摇杆移动 / 右摇杆滚轮在引擎内；此处为 L3/R3）
UNIVERSAL_MOUSE_MAPPINGS = {
    10: MOUSE_LEFT,
    11: MOUSE_RIGHT,
}

DEFAULT_MOUSE_SENSITIVITY = 20.0
DEFAULT_STICK_DEADZONE = 0.15
DEFAULT_SCROLL_SENSITIVITY = 0.35
MOUSE_SENSITIVITY_MIN = 5.0
MOUSE_SENSITIVITY_MAX = 50.0
SCROLL_SENSITIVITY_MIN = 0.1
SCROLL_SENSITIVITY_MAX = 2.0
LT_LONG_PRESS_SEC = 0.4

BUTTON_NAMES = [
    "A", "B", "X", "Y",
    "LB", "RB", "LT", "RT",
    "Back", "Start", "L3", "R3",
    "D-Pad Up", "D-Pad Down", "D-Pad Left", "D-Pad Right",
    "Left Stick Up", "Left Stick Down", "Left Stick Left", "Left Stick Right",
    "Right Stick Up", "Right Stick Down", "Right Stick Right", "Right Stick Left",
]

KEYBOARD_KEYS = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "space", "enter", "tab", "backspace", "delete",
    "pageup", "pagedown",
    "left", "right", "up", "down",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "shift", "ctrl", "alt",
    "cmd", "win", "super", "cmd_l", "cmd_r",
    "ctrl_l", "ctrl_r", "shift_l", "shift_r", "alt_l", "alt_r",
    "[", "]", "(", ")", "{", "}", ";", "'", ",", ".", "/", "\\", "-", "=", "`",
]

BTN_COLOR = {
    "A": "#4ecca3", "B": "#e94560", "X": "#4a9eff", "Y": "#ffc107",
    "LB": "#a78bfa", "RB": "#a78bfa", "LT": "#f97316", "RT": "#f97316",
    "Back": "#94a3b8", "Start": "#94a3b8", "L3": "#64748b", "R3": "#64748b",
    "D-Pad Up": "#38bdf8", "D-Pad Down": "#38bdf8",
    "D-Pad Left": "#38bdf8", "D-Pad Right": "#38bdf8",
    "Left Stick Up": "#64748b", "Left Stick Down": "#64748b",
    "Left Stick Left": "#64748b", "Left Stick Right": "#64748b",
    "Right Stick Up": "#64748b", "Right Stick Down": "#64748b",
    "Right Stick Right": "#64748b", "Right Stick Left": "#64748b",
}
DEFAULT_BTN_COLOR = "#4a9eff"

THEME = {
    "bg": "#0f0f1a",
    "panel": "#1a1a2e",
    "card": "#252542",
    "accent": "#00d4aa",
    "accent2": "#7c5cff",
    "danger": "#ff5c5c",
    "warn": "#ffb84d",
    "success": "#00d4aa",
    "text": "#ffffff",
    "subtext": "#a0a0b8",
    "dim": "#3a3a5c",
    "dark": "#12121f",
    "border": "#4a4a6a",
    "hover": "#353555",
}

DEFAULT_THRESHOLD = 0.5
