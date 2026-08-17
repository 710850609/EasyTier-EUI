#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CoreCliAdapter — CLI subprocess adapter for EasyTier Core"""
import json
import logging
import subprocess
import threading
from typing import Union

from http_dispatcher.dispatcher import HttpException
from utils import run_configs, process_util, et_run_info, check_peers, common_util
from utils.process_util import ProcessManager
from .interface import IEasyTierAdapter

logger = logging.getLogger(__name__)

# 延迟初始化：使用线程安全的单例模式
_pm = {}
_pm_lock = threading.Lock()

def _get_process_manager(profile: str = None) -> Union[ProcessManager]:
    """获取 ProcessManager 实例（延迟初始化，线程安全）"""
    if not profile:
        raise HttpException('validate.profile_required')
    pm_key = profile

    # 双重检查锁定模式，保证线程安全的同时提高性能
    cur_pm = _pm.get(pm_key)
    if cur_pm is not None:
        return cur_pm

    with _pm_lock:
        # 再次检查，防止在获取锁期间已被其他线程创建
        cur_pm = _pm.get(pm_key)
        if cur_pm is None:
            pid_file = run_configs.et_pid_file(profile)
            cur_pm = process_util.ProcessManager(pid_file.replace('.toml', ''))
            _pm[pm_key] = cur_pm
    return cur_pm


class CoreForegroundAdapter(IEasyTierAdapter):

    def __init__(self, cli_path: str, core_path: str):
        self._cli_path = cli_path
        self._core_path = core_path

    def get_version(self) -> str:
        try:
            result = subprocess.run(
                [self._core_path, '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().replace('easytier-core ', '')
            return "unknown"
        except Exception:
            return "unknown"

    def start_network(self, toml_path: str, instance_name: str) -> None:
        rpc_port = check_peers.get_available_port(start_port=16888)
        rpc_portal = f"127.0.0.1:{rpc_port}"
        info = et_run_info.get(instance_name)
        # 使用用列表传参，避免执行文件路径含空格，导致报错找不到文件
        cmd = [
            f"{self._core_path}",
            "-c",
            toml_path,
            "-r",
            rpc_portal,
            f"--file-log-dir", f"{run_configs.log_dir()}",
            f"--file-log-level", f"{info.log_level or 'error'}",
            f"--file-log-size", f"50"  # 单个文件日志大小，单位 MB，默认值为 100MB
        ]
        logging.info(f"启动ET命令: {cmd}")
        pm = _get_process_manager(instance_name)
        pm.start(cmd)
        et_run_info.save(instance_name, rpc_portal, info.autostart, False)

    def stop_network(self, instance_name: str) -> None:
        logging.info(f"停止ET配置: {instance_name}")
        pm = _get_process_manager(instance_name)
        pm.stop()

    def status(self, instance_name: str) -> bool:
        pm = _get_process_manager(instance_name)
        return pm.status()

    def get_peers(self, instance_name: str) -> list[dict]:
        info = et_run_info.get(instance_name)
        if not info:
            logger.debug(f"未找到配置元数据：{instance_name}")
            return []
        if not info.rpc_portal:
            logger.debug(f"元数据没有rpc信息：{info.__dict__}")
            return []
        cmd = f"{self._cli_path} -o json --rpc-portal {info.rpc_portal} peer"
        try:
            result = common_util.run_cmd(cmd)
            peer_list = json.loads(result)
            return peer_list
        except Exception as e:
            if str(e).find('failed to connect to server') > 0:
                logger.debug(str(e))
                return []
            raise e

    def change_log_level(self, log_level: str, **kwargs) -> None:
        log_level = 'disabled' if log_level == 'off' else log_level
        log_level = 'warning' if log_level == 'warn' else log_level
        rpc_portal = kwargs.get('rpc_portal')
        cmd = [
            f"{self._cli_path}",
            "--rpc-portal",
            rpc_portal,
            "logger",
            "set",
            log_level,
        ]
        logger.info(f"设置日志级别命令： {cmd}")
        common_util.run_cmd(cmd)