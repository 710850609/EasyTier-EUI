#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行配置
"""
import logging
import os
import platform
import sys
from pathlib import Path
from typing import Optional, List

from utils import log_util

FRONTEND_PATH = None
CONFIG_DIR = None
CORE_DIR = None
DATA_DIR = None
LOG_DIR = None

def is_fn_system():
    """
    检查是否为飞牛系统
    """
    kernel_version = platform.release()
    return kernel_version.lower().find('trim') != -1

def setup_env(init_logger: bool=True):
    global FRONTEND_PATH, CONFIG_DIR, CORE_DIR, DATA_DIR, LOG_DIR
    # 是否在 PyInstaller 打包环境中
    WORK_DIR = None
    is_local_mode = False
    if is_fn_system():
        TRIM_APPNAME = os.getenv('TRIM_APPNAME', 'EasyTier-Lite')
        TRIM_APPDEST = os.getenv('TRIM_APPDEST', f'/var/apps/{TRIM_APPNAME}/target')
        TRIM_PKGVAR = os.getenv('TRIM_PKGVAR', f'/var/apps/{TRIM_APPNAME}/var')
        TRIM_SHARE_DIR = os.getenv('TRIM_SHARE_DIR', f'/var/apps/{TRIM_APPNAME}/shares/{TRIM_APPNAME}')

        CONFIG_DIR = os.getenv('CONFIG_DIR', f"{TRIM_SHARE_DIR}/configs")
        CORE_DIR = os.getenv('CORE_DIR', f"{TRIM_APPDEST}/bin")
        DATA_DIR = os.getenv('DATA_DIR', f"{TRIM_PKGVAR}")
        LOG_DIR = os.getenv('LOG_DIR', f"{TRIM_PKGVAR}/logs")
    elif getattr(sys, 'frozen', False):
        # _MEIPASS 是 PyInstaller 解压资源的临时目录
        WORK_DIR = str(Path(os.path.dirname(sys.executable)).absolute())
        Path(WORK_DIR).mkdir(parents=True, exist_ok=True)
        FRONTEND_PATH = os.path.abspath(os.path.join(sys._MEIPASS, 'frontend'))
    else:
        is_local_mode = True
        project_root_path = Path(__file__).absolute().parent.parent.parent
        WORK_DIR = str(project_root_path.joinpath('temp').joinpath('EasyTier-Lite').absolute())
        Path(WORK_DIR).mkdir(parents=True, exist_ok=True)
        FRONTEND_PATH = str(project_root_path.joinpath('frontend').joinpath('dist'))

    if WORK_DIR:
        CORE_DIR = os.path.join(WORK_DIR, 'core')
        CONFIG_DIR = os.path.join(WORK_DIR, 'config')
        DATA_DIR = os.path.join(WORK_DIR, 'data')
        LOG_DIR = os.path.join(WORK_DIR, 'logs')

    Path(CORE_DIR).mkdir(parents=True, exist_ok=True)
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    if init_logger:
        log_level = logging.DEBUG if is_local_mode else logging.INFO
        log_util.setup_log(log_file=os.path.join(LOG_DIR, 'app.log'), log_level=log_level, enabled_console=is_local_mode)

    logging.info(f"FRONTEND_PATH: {FRONTEND_PATH}")
    logging.info(f"CORE_DIR: {CORE_DIR}")
    logging.info(f"CONFIG_DIR: {CONFIG_DIR}")
    logging.info(f"DATA_DIR: {DATA_DIR}")
    logging.info(f"LOG_DIR: {LOG_DIR}")


BUILD_VERSION = "0.6.020500"


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