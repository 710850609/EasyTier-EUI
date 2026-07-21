#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyTier FFI 桥接模块
Android 端通过 JNI 调用 Rust FFI 接口，替代 subprocess 方式
"""

import ctypes
import logging
import os
import platform
from ctypes import c_char_p, c_int, c_void_p, POINTER, Structure
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EasyTierConfig(Structure):
    _fields_ = [
        ("config_path", c_char_p),
        ("instance_name", c_char_p),
        ("listener_url", c_char_p),
        ("network_name", c_char_p),
        ("network_secret", c_char_p),
        ("dhcp", c_int),
        ("crypto", c_char_p),
        ("multi_thread", c_int),
        ("latency_first", c_int),
        ("enable_ipv6", c_int),
    ]


class EasyTierStatus(Structure):
    _fields_ = [
        ("running", c_int),
        ("peers_count", c_int),
        ("error_msg", c_char_p),
    ]


class EasyTierPeerInfo(Structure):
    _fields_ = [
        ("peer_id", c_char_p),
        ("ip_address", c_char_p),
        ("hostname", c_char_p),
        ("latency_ms", c_int),
        ("bytes_sent", c_int),
        ("bytes_received", c_int),
        ("connected", c_int),
    ]


class EasyTierBridge:
    _instance = None
    _lib = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._lib is not None:
            return
        self._load_library()

    def _load_library(self):
        lib_name = "libeasytier_ffi.so"
        lib_paths = [
            Path(__file__).parent / lib_name,
            Path(os.environ.get('EUI_LIB_DIR', '')) / lib_name,
        ]
        arch = platform.machine()
        if arch == 'aarch64':
            lib_paths.append(Path(__file__).parent / 'arm64-v8a' / lib_name)
        elif arch == 'armv7l':
            lib_paths.append(Path(__file__).parent / 'armeabi-v7a' / lib_name)
        for lib_path in lib_paths:
            if lib_path.exists():
                try:
                    self._lib = ctypes.CDLL(str(lib_path))
                    self._setup_functions()
                    logger.info(f"Loaded EasyTier FFI: {lib_path}")
                    return
                except OSError as e:
                    logger.warning(f"Failed to load {lib_path}: {e}")
        raise RuntimeError(f"Could not load {lib_name}")

    def _setup_functions(self):
        lib = self._lib
        lib.easy_tier_init.argtypes = [POINTER(EasyTierConfig)]
        lib.easy_tier_init.restype = c_int
        lib.easy_tier_start.argtypes = []
        lib.easy_tier_start.restype = c_int
        lib.easy_tier_stop.argtypes = []
        lib.easy_tier_stop.restype = c_int
        lib.easy_tier_get_status.argtypes = [POINTER(EasyTierStatus)]
        lib.easy_tier_get_status.restype = c_int
        lib.easy_tier_get_peers.argtypes = [POINTER(c_int)]
        lib.easy_tier_get_peers.restype = POINTER(EasyTierPeerInfo)
        lib.easy_tier_free_peers.argtypes = [POINTER(EasyTierPeerInfo), c_int]
        lib.easy_tier_free_peers.restype = None
        lib.easy_tier_get_version.argtypes = []
        lib.easy_tier_get_version.restype = c_char_p
        lib.easy_tier_set_log_level.argtypes = [c_int]
        lib.easy_tier_set_log_level.restype = None

    def init(self, config: Dict[str, Any]) -> int:
        if self._lib is None:
            return -1
        cfg = EasyTierConfig()
        cfg.config_path = config.get('config_path', '').encode('utf-8')
        cfg.instance_name = config.get('instance_name', 'default').encode('utf-8')
        cfg.listener_url = config.get('listener_url', 'tcp://0.0.0.0:11010').encode('utf-8')
        cfg.network_name = config.get('network_name', 'default').encode('utf-8')
        cfg.network_secret = config.get('network_secret', '').encode('utf-8')
        cfg.dhcp = 1 if config.get('dhcp', True) else 0
        cfg.crypto = config.get('crypto', 'none').encode('utf-8')
        cfg.multi_thread = 1 if config.get('multi_thread', True) else 0
        cfg.latency_first = 1 if config.get('latency_first', False) else 0
        cfg.enable_ipv6 = 1 if config.get('enable_ipv6', False) else 0
        return self._lib.easy_tier_init(cfg)

    def start(self) -> int:
        return self._lib.easy_tier_start() if self._lib else -1

    def stop(self) -> int:
        return self._lib.easy_tier_stop() if self._lib else -1

    def get_status(self) -> Optional[Dict[str, Any]]:
        if self._lib is None:
            return None
        status = EasyTierStatus()
        ret = self._lib.easy_tier_get_status(status)
        if ret != 0:
            return None
        return {
            'running': bool(status.running),
            'peers_count': status.peers_count,
            'error_msg': status.error_msg.decode('utf-8') if status.error_msg else '',
        }

    def get_peers(self) -> list:
        if self._lib is None:
            return []
        count = c_int()
        peers_ptr = self._lib.easy_tier_get_peers(count)
        if not peers_ptr or count.value == 0:
            return []
        peers = []
        for i in range(count.value):
            peer = peers_ptr[i]
            peers.append({
                'peer_id': peer.peer_id.decode('utf-8') if peer.peer_id else '',
                'ip_address': peer.ip_address.decode('utf-8') if peer.ip_address else '',
                'hostname': peer.hostname.decode('utf-8') if peer.hostname else '',
                'latency_ms': peer.latency_ms,
                'bytes_sent': peer.bytes_sent,
                'bytes_received': peer.bytes_received,
                'connected': bool(peer.connected),
            })
        self._lib.easy_tier_free_peers(peers_ptr, count)
        return peers

    def get_version(self) -> str:
        if self._lib is None:
            return 'unknown'
        result = self._lib.easy_tier_get_version()
        return result.decode('utf-8') if result else 'unknown'

    def set_log_level(self, level: int):
        if self._lib is not None:
            self._lib.easy_tier_set_log_level(level)


et_bridge = EasyTierBridge()