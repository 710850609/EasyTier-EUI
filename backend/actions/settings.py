#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import shutil
import sys
import time
from pathlib import Path

from http_dispatcher.dispatcher import HttpException
from utils import run_configs, github_util


def eui_info(*kwargs):
    platform = 'trim' if run_configs.is_fn_system() else sys.platform
    install_path = Path(run_configs.core_dir()).parent
    # 解析符号链接，获取真实路径
    install_path = install_path.resolve()
    return {
        'build_version': run_configs.build_version(),
        'install_path': str(install_path),
        'platform': platform,
    }

def github_mirrors(params:dict, *kwargs):
    try:
        params = params or {}
        refresh = params.get('refresh', 'false').lower() == 'true'
        url_list = github_util.get_proxy_urls(refresh=refresh)
        url_list = [ {**item, 'label': item.get('url').replace('https://', '')} for item in url_list]
        return url_list
    except Exception as e:
        logging.warning(f"读取代理配置失败: {e}")
        raise HttpException(f"读取代理配置失败: {e}") from e

def delete_cache(*kwargs):
    download_path = Path(run_configs.data_dir(), 'download')
    total_bytes = 0
    if download_path.exists():
        for entry in download_path.rglob('*'):
            try:
                if entry.is_file() and not entry.is_symlink():
                    total_bytes += entry.stat().st_size
            except (OSError, PermissionError):
                pass
    shutil.rmtree(download_path, ignore_errors=True)
    if total_bytes == 0:
        logging.info(f"删除缓存目录: {download_path}, 共删除 0 字节")
        return f"缓存已删除干净"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while total_bytes >= 1024 and i < len(units) - 1:
        total_bytes /= 1024
        i += 1
    size = f"{total_bytes:.2f} {units[i]}"
    logging.info(f"删除缓存目录: {download_path}, 共删除 {size}")
    return f"缓存已删除 {size}"

def shutdown(*kwargs):
    import os
    import threading
    logging.info("Received shutdown request, exiting...")

    def do_exit():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=do_exit, daemon=True).start()
    return {"status": "success", "message": "正在关闭服务..."}

