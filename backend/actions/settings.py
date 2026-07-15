#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import shutil
import sys
import time
from pathlib import Path

import tomlkit

from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import run_configs, github_util


def eui_info(*args, **kwargs):
    platform = 'trim' if run_configs.is_fn_system() else sys.platform
    install_path = Path(run_configs.core_dir()).parent
    # 解析符号链接，获取真实路径
    install_path = install_path.resolve()
    return {
        'build_version': run_configs.build_version(),
        'install_path': str(install_path),
        'platform': platform,
        'for_user': run_configs.is_fn_system() and run_configs.DEFAULT_TRIM_APPNAME == 'EasyTier-EUI.User',
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
        os.remove(eui_config_file)
        logging.info(f"删除配置文件: {eui_config_file}")
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

def shutdown(params=None, *args, **kwargs):
    import os
    import threading
    logging.info("Received shutdown request, exiting...")

    def do_exit():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=do_exit, daemon=True).start()
    return {"status": "success", "message": get_message('settings.shutting_down')}