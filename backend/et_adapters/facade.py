#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTierFacade — unified entry point with adapter auto-selection"""

import logging
import sys
import threading
from typing import Optional

import tomlkit

from et_adapters.core_background_adapter import CoreBackgroundAdapter
from utils import run_configs
from .core_adapter import CoreAdapter
from .ffi_adapter import FfiAdapter
from .interface import IEasyTierAdapter

logger = logging.getLogger(__name__)


class EasyTierFacade(IEasyTierAdapter):

    def __init__(self):
        if run_configs.IS_ANDROID:
        # if run_configs.IS_ANDROID or sys.platform == "win32":
            self._adapter = FfiAdapter()
        else:
            self._adapter = CoreAdapter()
        logger.info(f"use adapter: {self._adapter}")

    def get_version(self) -> str:
        return self._adapter.get_version()

    def start_network(self, toml_path: str, instance_name: str) -> None:
        self._adapter.start_network(toml_path, instance_name)

    def stop_network(self, instance_name: str) -> None:
        self._adapter.stop_network(instance_name)

    def status(self, instance_name: str) -> bool:
        return self._adapter.status(instance_name)

    def get_peers(self, instance_name: str) -> list[dict]:
        return self._adapter.get_peers(instance_name)

    def get_service_dapter(self) -> Optional[CoreBackgroundAdapter]:
        if isinstance(self._adapter, CoreAdapter):
            return self._adapter.get_service_adapter()
        return None

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        if isinstance(self._adapter, FfiAdapter):
            return self._adapter.set_tun_fd(instance_name, fd)
        else:
            logger.warning(f"current adapter is not FfiAdapter, cannot set_tun_fd")
            return -1

    def get_route_info(self, instance_name: str) -> Optional[str]:
        if isinstance(self._adapter, FfiAdapter):
            return self._adapter.get_route_info(instance_name)
        else:
            logger.warning(f"current adapter is not FfiAdapter, cannot get_route_info")
            return None



    # def get_network_infos(self, max_length: int = 10) -> Dict[str, NetworkInstanceInfo]:
    #     if not self._adapter:
    #         return {}
    #     return self._adapter.get_network_infos(max_length)
    #
    # def get_network_infos_raw(self, max_length: int = 10) -> Dict[str, Any]:
    #     if not self._adapter:
    #         return {}
    #     return self._adapter.get_network_infos_raw(max_length)

    # def collect_network_infos_json(self, max_length: int = 10) -> str:
    #     """Return network infos as JSON string for Kotlin monitor"""
    #     raw = self._adapter.get_network_infos_raw(max_length) if self._adapter else {}
    #     return json.dumps({"map": raw})

    # def get_peers1(self) -> list:
    #     raw = self._adapter.get_network_infos_raw(10) if self._adapter else {}
    #     peers = []
    #     for instance_data in raw.values():
    #         for pair in instance_data.get('peer_route_pairs') or []:
    #             route = pair.get('route') or {}
    #             peer = pair.get('peer') or {}
    #             conns = peer.get('conns') or []
    #             first_conn = conns[0] if conns else {}
    #             tunnel = first_conn.get('tunnel') or {}
    #             stats = first_conn.get('stats') or {}
    #             stun = route.get('stun_info') or {}
    #             ipv4_addr = route.get('ipv4_addr') or {}
    #             ipv4 = self._addr_to_ipv4(ipv4_addr.get('address', {}).get('addr', 0))
    #             peers.append({
    #                 'ipv4': ipv4,
    #                 'hostname': route.get('hostname', ''),
    #                 'cost': self._format_cost(route.get('cost', 0)),
    #                 'tunnel_proto': tunnel.get('tunnel_type', ''),
    #                 'lat_ms': self._latency_to_ms(stats.get('latency_us', 0)),
    #                 'loss_rate': first_conn.get('loss_rate', 0),
    #                 'rx_bytes': stats.get('rx_bytes', 0),
    #                 'tx_bytes': stats.get('tx_bytes', 0),
    #                 'nat_type': self._format_nat_type(stun.get('udp_nat_type', 0)),
    #                 'version': route.get('version', ''),
    #                 'cidr': ', '.join(route.get('proxy_cidrs') or []),
    #             })
    #     return peers

    # def get_current_instance(self) -> Optional[str]:
    #     if not self._current_instance_name:
    #         return None
    #     info = self.get_network_infos(10)
    #     if self._current_instance_name in info:
    #         return self._current_instance_name
    #     return None



_facade_instance: Optional[EasyTierFacade] = None
_facade_lock = threading.Lock()

def get_facade() -> EasyTierFacade:
    global _facade_instance
    if _facade_instance is None:
        with _facade_lock:
            if _facade_instance is None:
                _facade_instance = EasyTierFacade()
    return _facade_instance