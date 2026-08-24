# -*- coding: utf-8 -*-
"""配置持久化"""

import json
import os
from typing import Dict

from core.constants import CONFIG_DIR, CONFIG_FILE, DEFAULT_THRESHOLD


def _config_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, CONFIG_DIR, CONFIG_FILE)


def load_config() -> tuple[Dict[int, str], float]:
    """加载映射配置，返回 (mappings, threshold)"""
    path = _config_path()
    if not os.path.isfile(path):
        return {}, DEFAULT_THRESHOLD

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}, DEFAULT_THRESHOLD

    mappings: Dict[int, str] = {}
    raw = data.get("mappings", {})
    for key, value in raw.items():
        if value and value != "-":
            mappings[int(key)] = str(value)

    threshold = float(data.get("threshold", DEFAULT_THRESHOLD))
    return mappings, threshold


def save_config(mappings: Dict[int, str], threshold: float) -> None:
    """保存映射配置"""
    path = _config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = {
        "mappings": {str(k): v for k, v in sorted(mappings.items())},
        "threshold": threshold,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
