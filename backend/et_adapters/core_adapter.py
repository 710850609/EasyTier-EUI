#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CoreCliAdapter — CLI subprocess adapter for EasyTier Core"""

import logging
import os
import sys

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

    def get_service_adapter(self) -> CoreBackgroundAdapter:
        return self._background