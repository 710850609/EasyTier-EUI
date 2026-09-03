#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTierFacade — unified entry point with adapter auto-selection"""

import logging
import threading
from typing import Optional

from et_adapters.core_background_adapter import CoreBackgroundAdapter
from utils import run_configs, et_run_info, app_settings
from .core_adapter import CoreAdapter
from .ffi_adapter import FfiAdapter
from .interface import IEasyTierAdapter

logger = logging.getLogger(__name__)


class EasyTierFacade(IEasyTierAdapter):

    def __init__(self):
        default_mode = 'ffi' if run_configs.IS_ANDROID else 'core'
        et_mode = app_settings.get('et_mode', default_mode)
        if et_mode == 'ffi':
            self._adapter = FfiAdapter()
        else:
            self._adapter = CoreAdapter()
        logger.debug(f"use adapter: {self._adapter}")

    def get_version(self) -> str:
        return self._adapter.get_version()

    def start_network(self, toml_path: str, instance_name: str) -> None:
        self._adapter.start_network(toml_path, instance_name)
        et_run_info.set_running(instance_name, True)

    def stop_network(self, instance_name: str) -> None:
        self._adapter.stop_network(instance_name)
        et_run_info.set_running(instance_name, False)

    def status(self, instance_name: str) -> bool:
        return self._adapter.status(instance_name)

    def get_peers(self, instance_name: str, relay_path: bool = False, proxy_info: bool = True) -> list[dict]:
        return self._adapter.get_peers(instance_name, relay_path, proxy_info)

    def change_log_level(self, log_level: str, **kwargs) -> None:
        self._adapter.change_log_level(log_level, **kwargs)

    def get_logs(self, params: dict) -> dict:
        return self._adapter.get_logs(params)

    def get_service_adapter(self) -> Optional[CoreBackgroundAdapter]:
        if isinstance(self._adapter, CoreAdapter):
            return self._adapter.get_service_adapter()
        return None

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        if isinstance(self._adapter, FfiAdapter):
            return self._adapter.set_tun_fd(instance_name, fd)
        else:
            logger.warning(f"current adapter is not FfiAdapter, cannot set_tun_fd")
            return -1



_facade_instance: Optional[EasyTierFacade] = None
_facade_lock = threading.Lock()

def get_facade() -> EasyTierFacade:
    global _facade_instance
    if _facade_instance is None:
        with _facade_lock:
            if _facade_instance is None:
                _facade_instance = EasyTierFacade()
    return _facade_instance