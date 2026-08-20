#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os.path
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

from utils import run_configs, app_settings

# 全局标志，记录日志是否已配置
_log_setup_done = False

# 配置日志
# Windows 控制台编码处理
if sys.platform == 'win32' and sys.stdout:
    import io
    # 强制 stdout/stderr 使用 utf-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def setup_log(log_file:Optional[str] = None, log_level:Union[int, str, None] = None, enabled_console:bool = False):
    global _log_setup_done
    if _log_setup_done:
        return  # 已配置过，直接返回

    if log_level is None:
        log_level = app_settings.get('log_level', 'WARN')
    log_level = log_level.upper() if isinstance(log_level, str) else log_level

    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)


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
            maxBytes=20 * 1024 * 1024,
            backupCount=5,  # 保留5个备份
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    if enabled_console and sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)  # 默认输出到 sys.stderr
        console_handler.setLevel(log_level)  # 可选，设置控制台的最低级别
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _log_setup_done = True


def set_log_level(level: Union[int, str], logger_name: Optional[str] = None, excluded_console: Optional[bool] = None):
    """
    动态修改日志级别（运行时热切换）。

    :param level: logging.DEBUG / logging.INFO / 'DEBUG' / 'INFO' 等
    :param logger_name: None=root, 'myapp.database'=指定模块
    :param excluded_console: 是否排除控制台输出，默认 False
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    target = logging.getLogger(logger_name)
    target.setLevel(level)

    # 关键：同步修改该 logger 的所有 handler
    for handler in target.handlers:
        is_console = isinstance(handler, logging.StreamHandler) and handler.stream in (sys.stdout, sys.stderr)
        if is_console and excluded_console:
            continue
        handler.setLevel(level)

    # 如果修改的是 root，还要处理那些 propagate=True 的子 logger
    # （子 logger 本身没 handler，日志会冒泡到 root，所以改 root 就够了）
    target.info(
        "日志级别已切换为 %s [%s]",
        logging.getLevelName(level),
        logger_name or "root"
    )