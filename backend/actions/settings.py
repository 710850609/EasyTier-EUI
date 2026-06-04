#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import sys
import time
from pathlib import Path

from http_dispatcher.dispatcher import HttpException
from utils import run_configs, github_util, et_run_info


def eui_info(*kwargs):
    platform = 'trim' if run_configs.is_fn_system() else sys.platform
    install_path = Path(run_configs.core_dir()).parent
    if platform == 'trim':
        install_path = install_path.parent
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

def shutdown(*kwargs):
    import os
    import threading
    logging.info("Received shutdown request, exiting...")

    def do_exit():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=do_exit, daemon=True).start()
    return {"status": "success", "message": "正在关闭服务..."}

