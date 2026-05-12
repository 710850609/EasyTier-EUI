#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os.path
from pathlib import Path
from typing import Optional, Dict

from http_dispatcher.dispatcher import HttpException
from utils import run_configs

__data = None

class EtRunInfo:
    """
    et 运行信息
    """
    def __init__(self, profile:str, rpc_portal:str, autostart:bool, use_system_service:bool):
        self.profile = profile
        self.rpc_portal = rpc_portal
        self.autostart = autostart
        self.use_system_service = use_system_service


def save(profile:str, rpc_portal:str, autostart:bool, use_system_service:bool):
    if not profile:
        raise HttpException("profile cannot be None for save")
    data = __load_data() or {}
    if not data or not data.get(profile):
        info = EtRunInfo(profile, rpc_portal, autostart, use_system_service)
    else:
        info = data[profile]
        info.rpc_portal = rpc_portal if rpc_portal is not None else info.rpc_portal
        info.autostart = autostart if autostart is not None else info.autostart
        info.use_system_service = use_system_service if use_system_service is not None else info.use_system_service
    data[profile] = info
    __save_data(data)

def get(profile:str)-> Optional[EtRunInfo]:
    if not profile:
        return None
    data = __load_data() or {}
    info = data.get(profile)
    if info is None and Path(run_configs.et_config_file(profile)).exists():
        save(profile, None, False, False)
    return data.get(profile)


def remove(profile:str):
    if not profile:
        return
    data = __load_data() or {}
    if profile in data:
        del data[profile]
        __save_data(data)
        __load_data(reload=True)

def all() -> Dict[str, EtRunInfo]:
    return __load_data()

def is_use_system_service(profile:str)-> bool:
    if not profile:
        return False
    data = __load_data() or {}
    info = data.get(profile)
    return info is not None and info.use_system_service

def __load_data(reload=False) -> Dict[str, EtRunInfo]:
    global __data
    if __data is None:
        run_file = run_configs.et_run_file()
        if not os.path.exists(run_file):
            return {}
        with open(run_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, value in data.items():
                data[key] = EtRunInfo(**value)
            __data = data
    return __data

def __save_data(data:Dict[str, EtRunInfo]):
    run_file = run_configs.et_run_file()
    if not os.path.exists(run_file):
        Path(run_file).touch()
    with open(run_file, "w", encoding="utf-8") as f:
        serializable_data = {k: v.__dict__ for k, v in data.items()}
        json.dump(serializable_data, f, ensure_ascii=False, indent=4)