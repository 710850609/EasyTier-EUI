#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# 全局标志，记录日志是否已配置
_log_setup_done = False

# 配置日志
# Windows 控制台编码处理
if sys.platform == 'win32' and sys.stdout:
    import io
    # 强制 stdout/stderr 使用 utf-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def setup_log(log_file:Optional[str] = None, log_level:int = logging.INFO, enabled_console:bool = False):
    global _log_setup_done
    if _log_setup_done:
        return  # 已配置过，直接返回

    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #     datefmt='%Y-%m-%d %H:%M:%S',
    #     handlers=[
    #         logging.FileHandler(LOG_FILE, encoding='utf-8'),  # 输出到文件
    #         logging.StreamHandler(sys.stdout)  # 输出到控制台
    #     ]
    # )


    # 设置日志级别（可选，默认为 WARNING，需要调低才能看到 INFO 及以上）
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # 清除所有已有 handler

    #  设置格式并添加 handler
    formatter = logging.Formatter(
        fmt='%(asctime)s - [%(process)d] - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        # fmt='%(asctime)s - %(name)s - %(levelname)s - [%(process)d] - %(filename)s:%(lineno)d - %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        #  创建 RotatingFileHandler
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=20 * 1024 * 1024,  # 5 MB
            backupCount=5,  # 保留5个备份
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    if enabled_console and sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)  # 默认输出到 sys.stderr
        console_handler.setLevel(log_level)  # 可选，设置控制台的最低级别
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _log_setup_done = True