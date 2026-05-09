#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os.path
import sys
from pathlib import Path
from typing import Optional, Dict, Union

from backend.utils import et_run_info
from http_dispatcher.dispatcher import HttpException
from utils import run_configs, process_util, check_peers
from utils.process_util import ProcessManager

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
    info = EtRunInfo(profile, rpc_portal, autostart, use_system_service)
    data = __load_data() or {}
    data[info.profile] = info
    __save_data(data)

def get(profile:str)-> Optional[EtRunInfo]:
    if not profile:
        return None
    data = __load_data() or {}
    return data.get(profile)

def all() -> Dict[str, EtRunInfo]:
    return __load_data()

def is_use_system_service(profile:str)-> bool:
    if not profile:
        return False
    data = __load_data() or {}
    info = data.get(profile)
    return info is not None and info.use_system_service

def __load_data() -> Dict[str, EtRunInfo]:
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
        

# 延迟初始化：使用单例模式
_pm = {}
def _get_process_manager(profile: str = None) -> Union[ProcessManager]:
    """获取 ProcessManager 实例（延迟初始化）"""
    global _pm
    pm_key = 'default' if profile is None else profile
    cur_pm = _pm.get(pm_key)
    if cur_pm is None:
        pid_file = run_configs.et_pid_file(profile)
        cur_pm = process_util.ProcessManager(pid_file)
        _pm[pm_key] = cur_pm
    return cur_pm

class EtRunMgr:

    def status(self, profile: str):
        pm = _get_process_manager(profile)
        running = pm.status()
        return {'running': running}

    def stop(self, profile: str):
        logging.info('停止ET服务')
        pm = _get_process_manager(profile)
        pm.stop()

    def start(self, profile: str):
        logging.info('启动ET服务')
        config_file = run_configs.et_config_file(profile)
        if not Path(config_file).exists():
            raise HttpException(f"不存在配置文件，请先确认配置")
        ext = '.exe' if sys.platform == 'win32' else ''
        rpc_port = check_peers.get_available_port(start_port=16888)
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-core')}{ext} --config-file {config_file} --rpc-portal 127.0.0.1:{rpc_port}"
        logging.info(f"启动命令: {cmd}")
        pm = _get_process_manager(profile)
        pm.start(cmd)
        et_run_info.save(profile, )

    def restart(self, profile: str):
        pm = _get_process_manager(profile)
        logging.info(f"重启ET服务...")
        if pm.status():
            logging.info(f"停止ET服务...")
            pm.stop()
        logging.info(f"启动ET服务...")
        self.start(profile)

    def start_all(*kwargs):
        start(*kwargs)

    def stop_all(*kwargs):
        stop(*kwargs)