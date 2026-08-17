#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CoreCliAdapter — CLI subprocess adapter for EasyTier Core"""

import logging
import os
import sys
from typing import Optional

from et_adapters.core_background_adapter import CoreBackgroundAdapter
from et_adapters.core_foreground_adapter import CoreForegroundAdapter
from et_adapters.interface import IEasyTierAdapter
from utils import run_configs, et_run_info

logger = logging.getLogger(__name__)


class CoreAdapter(IEasyTierAdapter):

    def __init__(self):
        ext = ".exe" if sys.platform == "win32" else ""
        self._cli_path = os.path.join(run_configs.core_dir(), f'easytier-cli{ext}')
        self._core_path = os.path.join(run_configs.core_dir(), f'easytier-core{ext}')
        for path in [self._cli_path, self._core_path]:
            if not os.path.exists(path):
                raise RuntimeError(f"Path not found: {path}")
        self._background = CoreBackgroundAdapter(self._cli_path, self._core_path)
        self._foreground = CoreForegroundAdapter(self._cli_path, self._core_path)

    def get_version(self) -> str:
        return self._foreground.get_version()

    def start_network(self, toml_path: str, instance_name: str) -> None:
        info = et_run_info.get(instance_name)
        if info is not None and info.use_system_service:
            self._background.start_network(toml_path, instance_name)
        else:
            self._foreground.start_network(toml_path, instance_name)

    def stop_network(self, instance_name: str) -> None:
        info = et_run_info.get(instance_name)
        if info is not None and info.use_system_service:
            self._background.stop_network(instance_name)
        else:
            self._foreground.stop_network(instance_name)

    def status(self, instance_name: str) -> bool:
        info = et_run_info.get(instance_name)
        if info is not None and info.use_system_service:
            return self._background.system_service_status() == 1
        else:
            return self._foreground.status(instance_name)

    def get_peers(self, instance_name: str) -> list[dict]:
        return self._foreground.get_peers(instance_name)


    def change_log_level(self, log_level: str, **kwargs) -> None:
        infos = et_run_info.get_all()
        profiles_systemed = []
        profiles_no_systemed = []
        for info in infos.values():
            if info.use_system_service:
                profiles_systemed.append(info.profile)
            else:
                profiles_no_systemed.append(info.profile)
        need_stop_systemed = False
        for profile in profiles_systemed:
            if self._background.status(profile):
                need_stop_systemed = True
                break

        if len(profiles_systemed) > 0:
            if need_stop_systemed:
                self._background.stop_network('')
            self._background.system_service_uninstall()
            self._background.system_service_install(profiles_systemed, log_level)
            if need_stop_systemed:
                self._background.start_network('', '')

        for profile in profiles_no_systemed:
            info = et_run_info.get(profile)
            log_level = 'disabled' if log_level == 'off' else log_level
            log_level = 'warning' if log_level == 'warn' else log_level
            if info.rpc_portal is not None:
                self._foreground.change_log_level(log_level, rpc_portal=info.rpc_portal)


    def get_service_adapter(self) -> Optional[CoreBackgroundAdapter]:
        """
        获取支持系统服务的适配器
        """
        if run_configs.is_docker() or run_configs.is_fn_system():
            return None
        return self._background