#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTierFacade — unified entry point with adapter auto-selection"""

import json
import logging
import threading
from typing import Any, Dict, Optional

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

    def get_network_infos_raw(self, max_length: int = 10) -> Dict[str, Any]:
        if not self._adapter:
            return {}
        return self._adapter.get_network_infos_raw(max_length)

    def collect_network_infos_json(self, max_length: int = 10) -> str:
        """Return network infos as JSON string for Kotlin monitor"""
        raw = self._adapter.get_network_infos_raw(max_length) if self._adapter else {}
        return json.dumps({"map": raw})

    def get_version(self) -> str:
        if not self._adapter:
            return "unknown"
        return self._adapter.get_version()

    def _addr_to_ipv4(self, addr: int) -> str:
        if not addr:
            return ""
        return ".".join(str((addr >> (i * 8)) & 0xFF) for i in range(3, -1, -1))

    def _latency_to_ms(self, latency_us: int) -> int:
        if not latency_us or latency_us <= 0:
            return 0
        ms = latency_us / 1000
        return int(ms) if ms >= 1 else 1

    def _format_nat_type(self, nat_type: int) -> str:
        types = {0: "Unknown", 1: "FullCone", 2: "Restricted", 3: "PortRestricted", 4: "Symmetric"}
        return types.get(nat_type, "Unknown")

    def _format_cost(self, cost: int) -> str:
        if cost == 0:
            return "Local"
        if cost == 1:
            return "p2p"
        return f"relay{cost}"

    def get_peers(self) -> list:
        raw = self._adapter.get_network_infos_raw(10) if self._adapter else {}
        peers = []
        for instance_data in raw.values():
            for pair in instance_data.get('peer_route_pairs') or []:
                route = pair.get('route') or {}
                peer = pair.get('peer') or {}
                conns = peer.get('conns') or []
                first_conn = conns[0] if conns else {}
                tunnel = first_conn.get('tunnel') or {}
                stats = first_conn.get('stats') or {}
                stun = route.get('stun_info') or {}
                ipv4_addr = route.get('ipv4_addr') or {}
                ipv4 = self._addr_to_ipv4(ipv4_addr.get('address', {}).get('addr', 0))
                peers.append({
                    'ipv4': ipv4,
                    'hostname': route.get('hostname', ''),
                    'cost': self._format_cost(route.get('cost', 0)),
                    'tunnel_proto': tunnel.get('tunnel_type', ''),
                    'lat_ms': self._latency_to_ms(stats.get('latency_us', 0)),
                    'loss_rate': first_conn.get('loss_rate', 0),
                    'rx_bytes': stats.get('rx_bytes', 0),
                    'tx_bytes': stats.get('tx_bytes', 0),
                    'nat_type': self._format_nat_type(stun.get('udp_nat_type', 0)),
                    'version': route.get('version', ''),
                    'cidr': ', '.join(route.get('proxy_cidrs') or []),
                })
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