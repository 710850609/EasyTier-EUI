#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行配置
"""

import os
from pathlib import Path
from typing import Optional, List

TRIM_APPNAME = os.getenv('TRIM_APPNAME', 'EasyTier-Lite')
TRIM_APPDEST = os.getenv('TRIM_APPDEST', f'/var/apps/{TRIM_APPNAME}/target')
TRIM_PKGVAR = os.getenv('TRIM_PKGVAR', f'/var/apps/{TRIM_APPNAME}/var')
TRIM_SHARE_DIR = os.getenv('TRIM_SHARE_DIR', f'/var/apps/{TRIM_APPNAME}/shares/{TRIM_APPNAME}')

CONFIG_DIR = os.getenv('CONFIG_DIR', f"{TRIM_SHARE_DIR}/configs")
CORE_DIR = os.getenv('CORE_DIR', f"{TRIM_APPDEST}/bin")
DATA_DIR = os.getenv('DATA_DIR', f"{TRIM_PKGVAR}")
LOG_DIR = os.getenv('LOG_DIR', f"{TRIM_PKGVAR}/logs")

BUILD_VERSION = "0.6.020500"

class EtRunConfig:
    def __init__(self, data: dict):
        self.rpc = {}
        if data.get('rpc'):
            self.rpc['rpc'] = data['rpc']
        if data.get('log'):
            self.rpc['log'] = data['log']

def build_version():
    return BUILD_VERSION

def config_dir():
    return CONFIG_DIR

def core_dir():
    return CORE_DIR

def data_dir():
    return DATA_DIR

def log_dir():
    return LOG_DIR

def et_log_dir():
    return os.path.join(log_dir(), 'easytier')

def et_config_file(file_name=None):
    file_name = 'default.toml' if file_name is None else file_name
    return os.path.join(config_dir(), file_name)

def et_config_files() -> List[str]:
    config_dir_path = config_dir()
    if not os.path.exists(config_dir_path):
        return []
    config_files = []
    for file in os.listdir(config_dir_path):
        if Path(file).name.lower().endswith('.toml'):
            config_files.append(file)
    return config_files

def et_pid_file(profile: Optional[str]):
    file_name = 'app.pid' if profile is None else f"{profile}.pid"
    return os.path.join(data_dir(), file_name)

# def et_restart_flag_file():
#     return os.path.join(data_dir(), '.restart')

# def et_init_flag_file():
#     return os.path.join(data_dir(), '.init')

def et_peer_meta_file():
    return os.path.join(data_dir(), 'peer-txt-meta.json')

def github_proxy_file():
    return os.path.join(data_dir(), 'github_proxy_url.txt')

def et_run_file():
    return os.path.join(data_dir(), 'et_run.json')

def fn_check_file():
    """
    检查文件, 记录应用启动时的开机时间，用于检查是否已经启动过应用
    """
    return os.path.join(data_dir(), 'fn_check.txt')
