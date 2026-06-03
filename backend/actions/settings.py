#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from http_dispatcher.dispatcher import HttpException
from utils import run_configs, et_run_info, github_util


def eui_info(*kwargs):
    platform = 'trim' if run_configs.is_fn_system() else sys.platform
    return {
        'build_version': run_configs.build_version(),
        'install_path': str(Path(run_configs.core_dir()).parent),
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

