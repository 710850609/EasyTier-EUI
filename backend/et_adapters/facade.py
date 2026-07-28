#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTierFacade — unified entry point with adapter auto-selection"""

import json
import logging
import threading
from typing import Dict, Optional

from .interface import IEasyTierAdapter
from .models import NetworkInstanceInfo
from .ffi_main import FfiMainAdapter
from .ffi_adapter import FfiAdapter
from .core_cli import CoreCliAdapter

logger = logging.getLogger(__name__)


class EasyTierFacade(IEasyTierAdapter):

    ADAPTER_PRIORITY = [FfiMainAdapter, FfiAdapter, CoreCliAdapter]

    def __init__(self):
        self._adapter: Optional[IEasyTierAdapter] = None
        self._adapter_name: str = "none"
        self._current_instance_name: Optional[str] = None
        self._auto_select()

    def _auto_select(self):
        for cls in self.ADAPTER_PRIORITY:
            try:
                adapter = cls()
                if adapter.is_available():
                    self._adapter = adapter
                    self._adapter_name = cls.__name__
                    logger.info(f"Selected adapter: {self._adapter_name}")
                    return
            except Exception as e:
                logger.warning(f"Failed to init {cls.__name__}: {e}")
        logger.error("No adapter available")

    @property
    def adapter_name(self) -> str:
        return self._adapter_name

    @property
    def current_instance_name(self) -> Optional[str]:
        return self._current_instance_name

    @property
    def is_ffi(self) -> bool:
        return isinstance(self._adapter, (FfiMainAdapter, FfiAdapter))

    @property
    def is_available(self) -> bool:
        return self._adapter is not None

    def start_network(self, toml_path: str, instance_name: str) -> None:
        if not self._adapter:
            raise RuntimeError("No adapter available")
        self._current_instance_name = instance_name
        self._adapter.start_network(toml_path, instance_name)

    def stop_network(self, instance_name: str = None) -> None:
        if not self._adapter:
            raise RuntimeError("No adapter available")
        self._adapter.stop_network(instance_name)
        if instance_name is None or instance_name == self._current_instance_name:
            self._current_instance_name = None

    def get_network_infos(self, max_length: int = 10) -> Dict[str, NetworkInstanceInfo]:
        if not self._adapter:
            return {}
        return self._adapter.get_network_infos(max_length)

    def collect_network_infos_json(self, max_length: int = 10) -> str:
        """Return network infos as JSON string for Kotlin monitor"""
        infos = self.get_network_infos(max_length)
        return json.dumps({"map": {k: v.to_json_serializable() for k, v in infos.items()}})

    def get_version(self) -> str:
        if not self._adapter:
            return "unknown"
        return self._adapter.get_version()

    def get_peers(self) -> list:
        info = self.get_network_infos(10)
        peers = []
        for instance_data in info.values():
            for peer in instance_data.peers:
                peers.append(peer)
        return peers

    def get_current_instance(self) -> Optional[str]:
        if not self._current_instance_name:
            return None
        info = self.get_network_infos(10)
        if self._current_instance_name in info:
            return self._current_instance_name
        return None

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        if not self._adapter:
            raise RuntimeError("No adapter available")
        return self._adapter.set_tun_fd(instance_name, fd)


_facade_instance: Optional[EasyTierFacade] = None
_facade_lock = threading.Lock()


def get_facade() -> EasyTierFacade:
    global _facade_instance
    if _facade_instance is None:
        with _facade_lock:
            if _facade_instance is None:
                _facade_instance = EasyTierFacade()
    return _facade_instance