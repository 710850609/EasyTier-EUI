#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
此脚本为飞牛专用，主要用于避免空跑时，让飞牛按需识别为应用开启状态。方便进入界面操作
开启应用，没有et运行，识别为运行中
关闭应用，识别为停用
重启系统，根据上次运行状态，提供方法给飞牛拉起应用，并启动原来的运行服务
"""
import logging
import os.path
import sys
from pathlib import Path

import psutil

from actions import services
from utils import run_configs, log_util
from utils import common_util

_fn_check_file = run_configs.fn_check_file()

def status():
    """
    应用启动前检查一次
    应用运行期间定期轮询检查
    检查文件的开机时间是否为当前开机时间
    0 表示应用正在运行
    3 表示应用未运行
    """
    if not os.path.exists(_fn_check_file):
        return 3
    boot_time_timestamp = psutil.boot_time()
    with open(_fn_check_file, 'r') as f:
        data = f.readline()
        if data == str(boot_time_timestamp):
            return 0
        return 3

def start():
    """
    先调用 status(), 未执行时才调用 start()
    启动成功后，把 开机时间 写入 文件
    """
    Path(run_configs.config_dir()).mkdir(parents=True, exist_ok=True)
    services.start_all()
    check_file = Path(_fn_check_file)
    if not check_file.exists():
        check_file.touch()
    with open(_fn_check_file, 'w') as f:
        f.write(str(psutil.boot_time()))

def stop():
    """
    先调用 status(), 未执行时才调用 stop()
    停止应用，不设置
    """
    services.stop_all()
    Path(_fn_check_file).unlink(missing_ok=True)

def is_fn_system():
    """
    检查是否为飞牛系统
    """
    if sys.platform == "linux":
        kernel_version = common_util.run_cmd('uname', '-r')
        logging.info(f"kernel_version: {kernel_version}")
        return kernel_version.lower().find('trim') != -1
    return False

if __name__ == '__main__':
    try:
        log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'cmd.log'), log_level=logging.INFO, enabled_console=False)
        args = sys.argv
        if len(args) != 2:
            print(f"传入参数错误： {args}")
            sys.exit(1)
        method = args[1]
        if method == "start":
            start()
        elif method == "stop":
            stop()
        elif method == "status":
            result = status()
            sys.exit(result)
        else:
            raise AssertionError(f"不支持的参数 {method}")
    except Exception as e:
        logging.error(e)
        logging.exception(e)
        sys.exit(1)