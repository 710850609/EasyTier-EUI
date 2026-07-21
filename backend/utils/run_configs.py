#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行配置
"""
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

import tomlkit

IS_ANDROID = False

FRONTEND_PATH:str = None
CONFIG_DIR:str = None
CORE_DIR:str = None
DATA_DIR:str = None
LOG_DIR:str = None
UPGRADE_SCRIPT_PATH:str = None
DEFAULT_TRIM_APPNAME:str = 'EasyTier-EUI'
EUI_RUN_HOST:str = None
EUI_RUN_PORT:int = None
EUI_CONFIG_FILE:str = 'eui.toml'

_is_inited_evn = False
_run_mode = 0

def setup_env():
    global _is_inited_evn
    if _is_inited_evn:
        return
    global FRONTEND_PATH, CONFIG_DIR, CORE_DIR, DATA_DIR, LOG_DIR, UPGRADE_SCRIPT_PATH, _run_mode, DEFAULT_TRIM_APPNAME, \
        EUI_RUN_HOST, EUI_RUN_PORT, EUI_CONFIG_FILE, IS_ANDROID
    # Android 平台检测
    IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_ROOT' in os.environ
    if IS_ANDROID:
        data_dir = os.environ.get('EUI_DATA_DIR', '/data/data/com.easytier.eui/files')
        CONFIG_DIR = os.path.join(data_dir, 'config')
        DATA_DIR = os.path.join(data_dir, 'data')
        LOG_DIR = os.path.join(data_dir, 'log')
        CORE_DIR = os.path.join(data_dir, 'core')
        FRONTEND_PATH = os.environ.get('EUI_FRONTEND_DIR', os.path.join(data_dir, 'frontend'))
        UPGRADE_SCRIPT_PATH = ''
        EUI_CONFIG_FILE = os.path.join(CONFIG_DIR, 'eui.toml')
        EUI_RUN_HOST = '127.0.0.1'
        EUI_RUN_PORT = 0
        for d in [CONFIG_DIR, DATA_DIR, LOG_DIR, CORE_DIR]:
            os.makedirs(d, exist_ok=True)
        _is_inited_evn = True
        return
    # 是否在 PyInstaller 打包环境中
    WORK_DIR = None
    if is_fn_system():
        TRIM_APPNAME = os.getenv('TRIM_APPNAME', DEFAULT_TRIM_APPNAME)
        TRIM_APPDEST = os.getenv('TRIM_APPDEST', f'/var/apps/{TRIM_APPNAME}/target')
        TRIM_PKGVAR = os.getenv('TRIM_PKGVAR', f'/var/apps/{TRIM_APPNAME}/var')
        TRIM_SHARE_DIR = os.getenv('TRIM_SHARE_DIR', f'/var/apps/{TRIM_APPNAME}/shares/{TRIM_APPNAME}')

        CONFIG_DIR = os.getenv('CONFIG_DIR', f"{TRIM_SHARE_DIR}/configs")
        CORE_DIR = os.getenv('CORE_DIR', f"{TRIM_APPDEST}/bin")
        DATA_DIR = os.getenv('DATA_DIR', f"{TRIM_PKGVAR}")
        LOG_DIR = os.getenv('LOG_DIR', f"{TRIM_PKGVAR}/logs")
        FRONTEND_PATH = os.path.join(TRIM_APPDEST, 'frontend')
        _run_mode = 2
    elif getattr(sys, 'frozen', False):
        # _MEIPASS 是 PyInstaller 解压资源的临时目录
        WORK_DIR = str(Path(os.path.dirname(sys.executable)).absolute())
        Path(WORK_DIR).mkdir(parents=True, exist_ok=True)
        FRONTEND_PATH = os.path.abspath(os.path.join(sys._MEIPASS, 'frontend'))
        UPGRADE_SCRIPT_PATH = os.path.abspath(os.path.join(sys._MEIPASS, 'assets'))
        _run_mode = 1
    else:
        project_root_path = Path(__file__).absolute().parent.parent.parent
        WORK_DIR = str(project_root_path.joinpath('temp').joinpath('EasyTier-EUI').absolute())
        Path(WORK_DIR).mkdir(parents=True, exist_ok=True)
        FRONTEND_PATH = str(project_root_path.joinpath('frontend').joinpath('dist'))
        UPGRADE_SCRIPT_PATH = Path(__file__).absolute().parent.parent.joinpath('assets')
        _run_mode = 0

    if WORK_DIR:
        CORE_DIR = os.path.join(WORK_DIR, 'core')
        CONFIG_DIR = os.path.join(WORK_DIR, 'config')
        DATA_DIR = os.path.join(WORK_DIR, 'data')
        LOG_DIR = os.path.join(WORK_DIR, 'logs')
        EUI_CONFIG_FILE = os.path.join(WORK_DIR, EUI_CONFIG_FILE)
        if os.path.exists(EUI_CONFIG_FILE):
            with open(EUI_CONFIG_FILE, "r", encoding="utf-8") as f:
                eui_config = tomlkit.parse(f.read())
                server_config = eui_config.get('server', {})
                EUI_RUN_HOST = server_config.get('host', None)
                EUI_RUN_PORT = server_config.get('port', None)

    Path(CORE_DIR).mkdir(parents=True, exist_ok=True)
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    # if init_logger:
    #     log_level = logging.DEBUG if is_local_mode else logging.INFO
    #     log_util.setup_log(log_file=os.path.join(LOG_DIR, 'app.log'), log_level=log_level, enabled_console=is_local_mode)

    logging.info(f"FRONTEND_PATH: {FRONTEND_PATH}")
    logging.info(f"CORE_DIR: {CORE_DIR}")
    logging.info(f"CONFIG_DIR: {CONFIG_DIR}")
    logging.info(f"DATA_DIR: {DATA_DIR}")
    logging.info(f"LOG_DIR: {LOG_DIR}")
    _is_inited_evn = True


BUILD_VERSION = "1.4.020604-20260713130029"


def is_musl_sys():
    """检测当前 Linux 系统是否是 musl libc，跨平台安全"""
    if not sys.platform.startswith("linux"):
        return False
    try:
        result = subprocess.run(
            ['ldd', '--version'],
            capture_output=True,
            text=True,
            timeout=3
        )
        return 'musl' in (result.stdout + result.stderr)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def is_docker():
    if os.path.exists("/.dockerenv"):
       # 检查是否为 Docker 容器环境
       return True
    return False

def is_fn_system():
    """
    检查是否为飞牛系统
    等效 uname -r
    """
    if is_docker():
        return False
    kernel_version = platform.release()
    return kernel_version.lower().find('trim') != -1

def build_version() -> str:
    return BUILD_VERSION

def config_dir() -> str:
    return CONFIG_DIR

def core_dir() -> str:
    return CORE_DIR

def data_dir() -> str:
    return DATA_DIR

def log_dir() -> str:
    return LOG_DIR

def et_log_dir() -> str:
    return os.path.join(log_dir(), 'easytier')

def et_config_file(file_name=None) -> str:
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

def et_pid_file(profile: Optional[str]) -> str:
    file_name = 'app.pid' if profile is None else f"{profile}.pid"
    return os.path.join(data_dir(), file_name)

def et_peer_meta_file() -> str:
    return os.path.join(data_dir(), 'peer-txt-meta.json')

def et_peer_check_result_file() -> str:
    return os.path.join(data_dir(), 'peer-check-result.json')

def et_run_file() -> str:
    return os.path.join(data_dir(), 'et_run.json')

def fn_check_file() -> str:
    """
    检查文件, 记录应用启动时的开机时间，用于检查是否已经启动过应用
    """
    return os.path.join(data_dir(), 'fn_check.txt')

def get_run_mode() -> int:
    """
    获取运行模式
    0 ： 本地开发模式
    1 ： 打包模式
    2 ： 飞牛系统模式
    """
    return _run_mode

def upgrade_script_path() -> str:
    if sys.platform == 'win32':
        return os.path.join(UPGRADE_SCRIPT_PATH, 'upgrade.bat')
    else:
        return os.path.join(UPGRADE_SCRIPT_PATH, 'upgrade.sh')