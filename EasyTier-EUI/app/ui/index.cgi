#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import json

def setup_logger():
    from utils import log_util, run_configs
    run_configs.setup_env()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'), log_level=logging.INFO,
                       enabled_console=False)

def active_venv():
    # # 激活server虚拟环境
    backend_path = os.environ.get('BACKEND_PATH', os.path.join(os.path.dirname(__file__), '..', 'backend'))
    backend_path = os.path.abspath(backend_path)
    venv_path = os.path.join(backend_path, '.venv')
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = os.path.join(venv_path, 'lib', python_version, 'site-packages')
    if os.path.exists(site_packages):
        sys.path.insert(0, site_packages)
        bin_path = os.path.join(venv_path, 'bin')
        if os.path.exists(bin_path):
            os.environ['PATH'] = bin_path + ':' + os.environ.get('PATH', '')
    else:
        logging.error(f"找不到python依赖: {site_packages}")

    # 添加backend目录到Python路径
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

def dispatcher():
    from http_dispatcher import  dispatcher
    # os.environ['FRONTEND_PATH'] = f'/var/apps/EasyTier-EUI/target/frontend'
    dispatcher.http_handle(base_uri='/cgi/ThirdParty/EasyTier-EUI/index.cgi', cgi_module=True)

if __name__ == '__main__':
    try:
        active_venv()
        setup_logger()
        dispatcher()
    except Exception as e:
        logging.error(f"CGI服务异常",  exc_info=True)
        print(f"Status: 500")
        print("Content-Type: application/json; charset=utf-8")
        print("")
        print(json.dumps(e, ensure_ascii=False))