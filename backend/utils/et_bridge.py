#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyTier FFI 桥接模块
通过 ctypes 调用官方 easytier-ffi C ABI，替代 subprocess 方式
API 对应 EasyTier upstream: easytier-contrib/easytier-ffi/src/lib.rs
"""

import ctypes
import json
import logging
import os
import platform
from ctypes import c_char_p, c_int, c_void_p, POINTER, Structure, c_ulonglong
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class KeyValuePair(Structure):
    _fields_ = [
        ("key", c_char_p),
        ("value", c_char_p),
    ]


class EasyTierFFI:
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

        try:
            self._lib = ctypes.CDLL(lib_name)
            self._setup_functions()
            logger.info("Loaded EasyTier FFI via system library path")
            return
        except OSError as e:
            logger.warning(f"Failed to load via system path: {e}")

        raise RuntimeError(f"Could not load {lib_name}")

    def _setup_functions(self):
        lib = self._lib
        lib.parse_config.argtypes = [c_char_p]
        lib.parse_config.restype = c_int

        lib.run_network_instance.argtypes = [c_char_p]
        lib.run_network_instance.restype = c_int

        lib.retain_network_instance.argtypes = [POINTER(c_char_p), ctypes.c_size_t]
        lib.retain_network_instance.restype = c_int

        lib.delete_network_instance.argtypes = [POINTER(c_char_p), ctypes.c_size_t]
        lib.delete_network_instance.restype = c_int

        lib.collect_network_infos.argtypes = [POINTER(KeyValuePair), ctypes.c_size_t]
        lib.collect_network_infos.restype = c_int

        lib.list_instance.argtypes = [POINTER(KeyValuePair), ctypes.c_size_t]
        lib.list_instance.restype = c_int

        lib.set_tun_fd.argtypes = [c_char_p, c_int]
        lib.set_tun_fd.restype = c_int

        lib.call_json_rpc.argtypes = [c_char_p, c_char_p, c_char_p, c_char_p, POINTER(c_char_p)]
        lib.call_json_rpc.restype = c_int

        lib.get_error_msg.argtypes = []
        lib.get_error_msg.restype = c_char_p

        lib.free_string.argtypes = [c_char_p]
        lib.free_string.restype = None

    def get_last_error(self) -> str:
        if self._lib is None:
            return "FFI library not loaded"
        result = self._lib.get_error_msg()
        if result:
            return result.decode('utf-8', errors='replace')
        return ""

    def parse_config(self, toml_config: str) -> int:
        if self._lib is None:
            return -1
        return self._lib.parse_config(toml_config.encode('utf-8'))

    def run_network_instance(self, toml_config: str) -> int:
        if self._lib is None:
            return -1
        return self._lib.run_network_instance(toml_config.encode('utf-8'))

    def retain_network_instance(self, instance_names: List[str]) -> int:
        if self._lib is None:
            return -1
        if not instance_names:
            return self._lib.retain_network_instance(None, 0)
        encoded = [name.encode('utf-8') for name in instance_names]
        arr = (c_char_p * len(encoded))(*encoded)
        return self._lib.retain_network_instance(arr, len(encoded))

    def stop_all_instances(self) -> int:
        return self.retain_network_instance([])

    def delete_network_instance(self, instance_names: List[str]) -> int:
        if self._lib is None:
            return -1
        if not instance_names:
            return 0
        encoded = [name.encode('utf-8') for name in instance_names]
        arr = (c_char_p * len(encoded))(*encoded)
        return self._lib.delete_network_instance(arr, len(encoded))

    def collect_network_infos(self, max_length: int = 10) -> Dict[str, Any]:
        if self._lib is None:
            return {}
        infos = (KeyValuePair * max_length)()
        count = self._lib.collect_network_infos(infos, max_length)
        if count < 0:
            raise RuntimeError(f"collect_network_infos failed: {self.get_last_error()}")
        result = {}
        for i in range(min(count, max_length)):
            key = infos[i].key.decode('utf-8') if infos[i].key else ""
            value = infos[i].value.decode('utf-8') if infos[i].value else ""
            try:
                result[key] = json.loads(value)
            except json.JSONDecodeError:
                result[key] = value
            self._lib.free_string(infos[i].key)
            self._lib.free_string(infos[i].value)
        return result

    def list_instance(self, max_length: int = 10) -> Dict[str, str]:
        if self._lib is None:
            return {}
        infos = (KeyValuePair * max_length)()
        count = self._lib.list_instance(infos, max_length)
        if count < 0:
            raise RuntimeError(f"list_instance failed: {self.get_last_error()}")
        result = {}
        for i in range(min(count, max_length)):
            key = infos[i].key.decode('utf-8') if infos[i].key else ""
            value = infos[i].value.decode('utf-8') if infos[i].value else ""
            result[key] = value
            self._lib.free_string(infos[i].key)
            self._lib.free_string(infos[i].value)
        return result

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        if self._lib is None:
            return -1
        return self._lib.set_tun_fd(instance_name.encode('utf-8'), fd)

    def call_json_rpc(self, service_name: str, method_name: str,
                      payload_json: str, domain_name: str = None) -> Optional[str]:
        if self._lib is None:
            return None
        out = c_char_p()
        ret = self._lib.call_json_rpc(
            service_name.encode('utf-8'),
            method_name.encode('utf-8'),
            (domain_name or "").encode('utf-8'),
            payload_json.encode('utf-8'),
            ctypes.byref(out)
        )
        if ret != 0:
            raise RuntimeError(f"call_json_rpc failed: {self.get_last_error()}")
        result = out.value.decode('utf-8') if out.value else ""
        self._lib.free_string(out)
        return result

    def get_version(self) -> str:
        info = self.collect_network_infos(1)
        if info:
            inst = next(iter(info.values()), {})
            if isinstance(inst, dict):
                return inst.get('version', 'unknown')
        return 'unknown'

    def get_status(self) -> Optional[Dict[str, Any]]:
        info = self.collect_network_infos(1)
        if not info:
            return None
        inst = next(iter(info.values()), {})
        if isinstance(inst, dict):
            return {
                'running': inst.get('running', False),
                'peers_count': len(inst.get('peer_nodes', [])),
                'error_msg': inst.get('error_msg', ''),
            }
        return None

    def get_peers(self) -> list:
        info = self.collect_network_infos(1)
        if not info:
            return []
        inst = next(iter(info.values()), {})
        if isinstance(inst, dict):
            peers = []
            for node in inst.get('peer_nodes', []):
                peers.append({
                    'peer_id': node.get('peer_id', ''),
                    'ip_address': node.get('virtual_ipv4', ''),
                    'hostname': node.get('hostname', ''),
                    'latency_ms': node.get('latency_ms', 0),
                    'bytes_sent': node.get('bytes_sent', 0),
                    'bytes_received': node.get('bytes_received', 0),
                    'connected': node.get('connected', False),
                })
            return peers
        return []


et_bridge = EasyTierFFI()