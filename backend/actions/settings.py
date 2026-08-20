#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

import tomlkit

from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import run_configs, github_util, log_util, app_settings

logger = logging.getLogger(__name__)

def eui_info(*args, **kwargs):
    platform = 'trim' if run_configs.is_fn_system() else sys.platform
    platform = 'android' if run_configs.IS_ANDROID else platform
    install_path = Path(run_configs.log_dir()).parent
    # 解析符号链接，获取真实路径
    install_path = install_path.resolve()
    is_docker = run_configs.is_docker()
    return {
        'build_version': run_configs.build_version(),
        'install_path': str(install_path),
        'platform': platform,
        'for_user': run_configs.is_fn_system() and run_configs.DEFAULT_TRIM_APPNAME == 'EasyTier-EUI.User',
        'is_docker': is_docker,
        'log_level': get_log_level(),
        'enabled_start_recovery': app_settings.get('enabled_start_recovery', False)
    }

def github_mirrors(params:dict, *args, **kwargs):
    try:
        params = params or {}
        refresh = params.get('refresh', 'false').lower() == 'true'
        url_list = github_util.get_proxy_urls(refresh=refresh)
        url_list = [ {**item, 'label': item.get('url').replace('https://', '')} for item in url_list]
        return url_list
    except Exception as e:
        logging.warning(f"读取代理配置失败: {e}")
        raise HttpException(get_message('settings.proxy_config_failed', error=str(e))) from e

def release_eui_config(params=None, *args, **kwargs):
    if run_configs.is_fn_system():
        raise HttpException(get_message('settings.current_system_not_support'))
    eui_config_file = run_configs.EUI_CONFIG_FILE
    if os.path.exists(eui_config_file):
        return get_message('settings.eui_config_file_exists', path=eui_config_file)
    doc = {
        'server': {
            'host': '0.0.0.0',
            'port': 5666,
            }
        }
    with open(eui_config_file, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))
        logging.info(f"生成配置文件: {eui_config_file}")
        if sys.platform != 'win32':
            os.chmod(eui_config_file, 0o666)
    return get_message('settings.eui_config_released', path=eui_config_file)

def delete_cache(params=None, *args, **kwargs):
    download_path = Path(run_configs.data_dir(), 'download')
    total_bytes = _delete_dir(download_path)
    logging.info(f"删除缓存目录: {download_path}, 累计删除 {total_bytes} 字节")
    tasks_path = Path(run_configs.data_dir(), 'tasks')
    total_bytes += _delete_dir(tasks_path)
    logging.info(f"删除任务目录: {tasks_path}, 累计删除 {total_bytes} 字节")
    if total_bytes == 0:
        return get_message('settings.cache_cleared')
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while total_bytes >= 1024 and i < len(units) - 1:
        total_bytes /= 1024
        i += 1
    size = f"{total_bytes:.2f} {units[i]}"
    logging.info(f"删除缓存目录: {download_path}, 任务目录: {tasks_path}, 累计删除 {size}")
    return get_message('settings.cache_deleted', size=size)

def _delete_dir(delete_path: Path):
    total_bytes = 0
    if delete_path.exists():
        for entry in delete_path.rglob('*'):
            try:
                if entry.is_file() and not entry.is_symlink():
                    total_bytes += entry.stat().st_size
            except (OSError, PermissionError):
                pass
    shutil.rmtree(delete_path, ignore_errors=True)
    return total_bytes

def delete_log(params=None, *args, **kwargs):
    log_path = Path(run_configs.log_dir())
    total_bytes = 0
    if log_path.exists():
        for entry in log_path.iterdir():
            if entry.is_file():
                try:
                    total_bytes += entry.stat().st_size
                    entry.write_text('', encoding='utf-8')
                except (OSError, PermissionError):
                    pass
    if total_bytes == 0:
        return get_message('settings.logDeleted')
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = total_bytes
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    size_str = f"{size:.2f} {units[i]}"
    logging.info(f"清空日志目录: {log_path}, 累计释放 {size_str}")
    return get_message('settings.log_deleted', size=size_str)

def get_log_level(params=None, *args, **kwargs):
    return app_settings.get('log_level', 'warn')

def set_log_level(params=None, *args, **kwargs):
    params = params or {}
    log_level = params.get('log_level', 'info').upper()
    try:
        if run_configs.IS_ANDROID:
            from java import jclass
            MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
            manager = MainActivity.getEasyTierManager()
            if manager is not None:
                manager.setLogLevel(log_level)
    except Exception as e:
        logger.exception(f"fail to set android log level: {e}")
    excluded_console = run_configs.is_docker()
    # docker 环境下，不修改 console 日志输出，方便控制台定位问题
    log_util.set_log_level(log_level, None, excluded_console)
    app_settings.save('log_level', log_level.lower())

def enabled_start_recovery(params=None, *args, **kwargs):
    params = params or {}
    enabled = params.get('enabled', False)
    if enabled != app_settings.get('enabled_start_recovery', False):
        app_settings.save('enabled_start_recovery', enabled)

def shutdown(params=None, *args, **kwargs):
    import os
    import threading
    logging.info("Received shutdown request, exiting...")

    def do_exit():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=do_exit, daemon=True).start()
    return {"status": "success", "message": get_message('settings.shutting_down')}