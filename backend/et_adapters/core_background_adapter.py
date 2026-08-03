#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTier Core Background Run Model"""

import logging
from pathlib import Path
from typing import Set, List

from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import run_configs, et_run_info, check_peers, common_util
from .core_foreground_adapter import CoreForegroundAdapter

logger = logging.getLogger(__name__)


def __get_system_service_profiles(self) -> Set[str]:
    auto_start_set = set()
    for config_file, item in et_run_info.get_all().items():
        if item.autostart:
            if Path(run_configs.et_config_file(config_file)).exists():
                auto_start_set.add(config_file)
            else:
                logging.warning(f"跳过并移除不存在的配置: {config_file}")
                et_run_info.remove(config_file)
    return auto_start_set

class CoreBackgroundAdapter(CoreForegroundAdapter):

    def __init__(self, cli_path: str, core_path: str):
        super().__init__(cli_path, core_path)
        self._cli_path = cli_path
        self._core_path = core_path

    def status(self, instance_name: str) -> bool:
        return self.system_service_status() == 1

    def start_network(self, toml_path: str, instance_name: str) -> None:
        if self.system_service_status() == -1:
            raise HttpException(get_message('service.not_registered'))
        cmd = f"{self._cli_path} service start"
        result = common_util.run_cmd(cmd)
        logging.info(f"ET系统服务启动结果：{result}")

    def stop_network(self, instance_name: str) -> None:
        if self.system_service_status() == -1:
            logging.warning(f"未注册ET系统服务，跳过停止服务")
            return
        cmd = f"{self._cli_path} service stop"
        logging.info(f"停止ET服务: {cmd}")
        common_util.run_cmd(cmd)


    def system_service_install(self, profiles: List[str], log_level:str = 'error') -> str:
        if len(profiles or []) == 0:
            raise AssertionError(get_message('service.no_config_for_system_service'))
        cmd_config_file_parts = ''
        for profile in profiles:
            cfg_path = run_configs.et_config_file(profile)
            if Path(cfg_path).exists():
                cmd_config_file_parts += f" -c {cfg_path}"
            else:
                logging.warning(f"跳过配置不存在: {profile}")
        desc = get_message('service.start_config_desc') + f":{','.join(profiles)}"
        display_name = "EasyTier-EUI"
        rpc_port = check_peers.get_available_port(start_port=16999)
        rpc_portal = f"127.0.0.1:{rpc_port}"
        cmd = (f"{self._cli_path} service install "
               f' --display-name {display_name}'
               f' --description {desc}'
               f" --core-path {self._core_path}"
               f" --service-work-dir {run_configs.data_dir()}"
               f" --rpc-portal {rpc_portal}"
               f" {cmd_config_file_parts}"
               f" --file-log-dir {run_configs.log_dir()}"
               f" --file-log-level {log_level or 'error'}"
               f" --file-log-size 50" # 单个文件日志大小，单位 MB，默认值为 100MB
               )
        logging.info(f"注册服务命令： {cmd}")
        result = common_util.run_cmd(cmd)
        logging.info(f"ET系统服务注册结果：{result}")
        for profile in profiles:
            p = et_run_info.get(profile)
            p.rpc_portal = rpc_portal
            p.autostart = True
            p.use_system_service = True
            et_run_info.save(*p.__dict__.values())
        return rpc_portal

    def system_service_uninstall(self):
        cmd = f"{self._cli_path} service uninstall"
        common_util.run_cmd(cmd)

    def system_service_status(self) -> int:
        """
        -1: 未注册
        0：未运行
        1：运行中
        """
        cmd = f"{self._cli_path} service status"
        result = common_util.run_cmd(cmd)
        logging.info(f"ET系统服务运行状态：{result}")
        if result.find('stopped') > 0:
            return 0
        elif result.find('running') > 0:
            return 1
        elif result.find('not installed') > 0:
            return -1
        else:
            raise HttpException(get_message('service.unknown_status', status=result))