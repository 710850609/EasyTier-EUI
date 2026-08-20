#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置
"""
import json
import os
from typing import Optional, Any

from utils import run_configs

_settings = {}

def _setting_file() -> str:
    return os.path.join(run_configs.data_dir(), 'setting.json')

def _load_data():
    global _settings
    if not _settings:
        settings_file = _setting_file()
        _settings = {}
        if os.path.exists(settings_file):
            with open(settings_file, "r", encoding="utf-8") as f:
                _settings = json.load(f)
    return _settings

def get(key: Optional[str] = None, default_value: Any = None) -> Any:
    data = _load_data().copy()
    if not key:
        return data
    if key not in data or data.get(key) is None:
        return default_value
    return data.get(key)

def save(key: str, value: str | dict | list) -> None:
    settings = _load_data()
    settings[key] = value
    with open(_setting_file(), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)