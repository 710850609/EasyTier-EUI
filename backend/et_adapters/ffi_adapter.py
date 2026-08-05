#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FfiAdapter — current default FFI adapter for v2.4.5/v2.6.4"""
import ctypes
import json
import logging
import os
import sys
import threading
import time
from ctypes import c_char_p, c_int, c_void_p, POINTER, Structure, c_size_t
from typing import Dict, Any, List, Set, Optional

import tomlkit

from utils import run_configs
from et_adapters.interface import IEasyTierAdapter

logger = logging.getLogger(__name__)
_FFI_LIB_VERSION = "unknown"
_MAX_INSTANCE_COUNT = 20

class KeyValuePair(Structure):
    _fields_ = [("key", c_void_p), ("value", c_void_p)]


class FfiAdapter(IEasyTierAdapter):

    REQUIRED_SYMBOLS = [
        'parse_config',
        'run_network_instance',
        'retain_network_instance',
        'collect_network_infos',
        'set_tun_fd',
        'get_error_msg',
        'free_string',
    ]
    MISSING_SYMBOLS: List[str] = []

    def __init__(self):
        lib_name = "libeasytier_ffi.so"
        if sys.platform == "win32":
            lib_name = os.path.join(run_configs.core_dir(), "easytier_ffi.dll")
        self._lib = ctypes.CDLL(lib_name)
        self._setup_functions()
        logger.info(f"Loaded EasyTier FFI: {lib_name}")
        self._lock = threading.RLock()
        self._instance_set: Set[str] = set()

    def _has_symbol(self, name: str) -> bool:
        try:
            getattr(self._lib, name)
            return True
        except AttributeError:
            return False

    def _setup_functions(self):
        for symbol in self.REQUIRED_SYMBOLS:
            if not self._has_symbol(symbol):
                raise RuntimeError(f"EasyTier FFI symbol not found: {symbol}")
        lib = self._lib
        if self._has_symbol('parse_config'):
            lib.parse_config.argtypes = [c_char_p]
            lib.parse_config.restype = c_int
        if self._has_symbol('run_network_instance'):
            lib.run_network_instance.argtypes = [c_char_p]
            lib.run_network_instance.restype = c_int
        if self._has_symbol('retain_network_instance'):
            lib.retain_network_instance.argtypes = [POINTER(c_char_p), c_size_t]
            lib.retain_network_instance.restype = c_int
        if self._has_symbol('collect_network_infos'):
            lib.collect_network_infos.argtypes = [POINTER(KeyValuePair), c_size_t]
            lib.collect_network_infos.restype = c_int
        if self._has_symbol('set_tun_fd'):
            lib.set_tun_fd.argtypes = [c_char_p, c_int]
            lib.set_tun_fd.restype = c_int
        if self._has_symbol('get_error_msg'):
            lib.get_error_msg.argtypes = [POINTER(c_char_p)]
            lib.get_error_msg.restype = None
        if self._has_symbol('free_string'):
            lib.free_string.argtypes = [c_void_p]
            lib.free_string.restype = None


    def get_version(self) -> str:
        return _FFI_LIB_VERSION

    def start_network(self, toml_path: str, instance_name: str) -> None:
        logger.info(f"start_network {instance_name}")
        try:
            with open(toml_path, 'r', encoding='utf-8') as f:
                toml_config = f.read()
            doc = tomlkit.parse(toml_config)
            flags = doc.get('flags', {})
            if 'compression' in flags:
                compression = flags['compression']
                if compression:
                    flags['data_compress_algo'] = compression.capitalize()
                del flags['compression']
                doc['flags'] = flags
                toml_config = tomlkit.dumps(doc)
            ret = self._parse_config(toml_config)
            if ret != 0:
                raise RuntimeError(f"Config parse failed: {self._get_last_error()}")
            if run_configs.IS_ANDROID:
                # 安卓环境下，确保所有实例都停止，再启动新实例
                self._retain_instances([])
                self._instance_set.clear()
            with self._lock:
                toml_bytes = toml_config.encode('utf-8')
                c_config = ctypes.c_char_p(toml_bytes)
                ret = self._lib.run_network_instance(c_config)
                if ret != 0:
                    raise RuntimeError(f"run_network_instance failed: {self._get_last_error()}")
            self._instance_set.add(instance_name)
            # 等待实例分配到虚拟ipv4（这里可等可不等）
            time.sleep(2.0)
            logger.info(f"Instance '{instance_name}' started via FFI")
            # 触发 Android VPN 授权弹窗并启动 dummy VPN + 监控
            try:
                if run_configs.IS_ANDROID:
                    from java import jclass
                    MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
                    manager = MainActivity.getEasyTierManager()
                    if manager is not None:
                        manager.start(instance_name)
            except Exception as e:
                logger.exception(f"fail to start vpn manager for instance '{instance_name}': {e}")
        except Exception as e:
            logger.exception(f"start_network failed: {e}")
            raise

    def stop_network(self, instance_name: str = None) -> None:
        logger.info(f"stop_network {instance_name}")
        all_instances = self._list_all_instance_names()
        keep = [n for n in all_instances if n != instance_name]
        self._retain_instances(keep)
        if instance_name in self._instance_set:
            self._instance_set.remove(instance_name)

        # 停止 Android VPN 监控和服务
        try:
            if run_configs.IS_ANDROID:
                from java import jclass
                MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
                manager = MainActivity.getEasyTierManager()
                if manager is not None:
                    manager.stop()
        except Exception as e:
            logger.exception(f"fail to stop vpn manager monitor: {e}")

    def status(self, instance_name: str) -> bool:
        return instance_name in self._instance_set

    def get_peers(self, instance_name: str) -> list[dict]:
        raw = self._collect_via_raw_ffi()
        instance_infos = raw.get(instance_name, {})
        peers = []
        my_node_info = instance_infos.get('my_node_info', {})
        if my_node_info:
            ipv4_addr = my_node_info.get('virtual_ipv4') or {}
            addr = (ipv4_addr.get('address') or {}).get('addr', 0)
            ipv4 = self._addr_to_ipv4(addr)
            network_len = ipv4_addr.get('network_length') or ''
            cidr = f"{ipv4}/{network_len}" if ipv4 else ''
            peers.append({
                'ipv4': ipv4,
                'cidr': cidr,
                'hostname': my_node_info.get('hostname') or '',
                'version': my_node_info.get('version') or '',
                'cost': 'Local',
                'tunnel_proto': '-',
                'lat_ms': "-",
                'loss_rate': "-",
                'rx_bytes': self._humanize_bytes(0),
                'tx_bytes': self._humanize_bytes(0),
                'nat_type': self._format_nat_type(my_node_info.get('stun_info', {}).get('udp_nat_type', 0)),
            })
        for pair in instance_infos.get('peer_route_pairs', []):
            route = pair.get('route') or {}
            peer = pair.get('peer') or {}
            conns = peer.get('conns') or []
            first_conn = conns[0] if conns else {}
            tunnel = first_conn.get('tunnel') or {}
            stats = first_conn.get('stats') or {}
            ipv4_addr = route.get('ipv4_addr') or {}
            ipv4 = self._addr_to_ipv4(ipv4_addr.get('address', {}).get('addr', 0))
            cidr = f"{ipv4}/{ipv4_addr.get('network_length', '')}" if ipv4 else ''
            stun = route.get('stun_info') or {}
            peers.append({
                'ipv4': ipv4,
                'cidr': cidr,
                'hostname': route.get('hostname') or '',
                'version': route.get('version') or '',
                'cost': self._format_cost(route.get('cost', 0)),
                'tunnel_proto': tunnel.get('tunnel_type') or '',
                'lat_ms': self._latency_to_ms(stats.get('latency_us', 1000000)),
                'loss_rate': f"{first_conn.get('loss_rate', 0)}%",
                'rx_bytes': self._humanize_bytes(stats.get('rx_bytes', 0)),
                'tx_bytes': self._humanize_bytes(stats.get('tx_bytes', 0)),
                'nat_type': self._format_nat_type(stun.get('udp_nat_type', 0)),
            })
        return peers

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        logger.info(f"set_tun_fd {instance_name} {fd}")
        if not self._has_symbol('set_tun_fd'):
            raise RuntimeError("set_tun_fd symbol not available")
        try:
            with self._lock:
                name_bytes = instance_name.encode('utf-8')
                c_name = ctypes.c_char_p(name_bytes)
                ret = self._lib.set_tun_fd(c_name, fd)
                if ret != 0:
                    raise RuntimeError(f"set_tun_fd failed: {self._get_last_error()}")
                return 0
        except RuntimeError as e:
            logger.exception(f"set_tun_fd runtime error: {e}")
            raise
        except Exception as e:
            raise RuntimeError(f"set_tun_fd failed: {e}") from e

    def get_route_info(self, instance_name: str) -> Optional[str]:
        try:
            info = {
                'virtual_ipv4': '',
                'dns_servers': ['223.5.5.5', '119.29.29.29', '114.114.114.114', '8.8.8.8'],
                'routes': [],
                'total_upload': '',
                'total_download': '',
            }
            total_upload = 0
            total_download = 0
            raw = self._collect_via_raw_ffi()
            instance_infos = raw.get(instance_name, {})
            my_node_info = instance_infos.get('my_node_info', {})
            virtual_ipv4 = my_node_info.get('virtual_ipv4') or {}
            addr = (virtual_ipv4.get('address') or {}).get('addr', 0)
            addr_str = self._addr_to_ipv4(addr)
            network_len = virtual_ipv4.get('network_length') or '24'
            info['virtual_ipv4'] = f"{addr_str}/{network_len}" if addr_str else ""
            routes = instance_infos.get('routes') or []
            for route in routes:
                cidrs = route.get('proxy_cidrs') or []
                for cidr in cidrs:
                    info['routes'].append(cidr)
            for peer in (instance_infos.get('peers') or []):
                for conn in (peer.get('conns') or []):
                    stats = conn.get('stats') or {}
                    total_download += stats.get('rx_bytes', 0) # 下载
                    total_upload += stats.get('tx_bytes', 0) # 上传
            info['total_upload'] = self._humanize_bytes(total_upload, for_short=True)
            info['total_download'] = self._humanize_bytes(total_download, for_short=True)
            return info
        except Exception as e:
            logger.exception(f"get_route_info failed: {e}")



    def _parse_config(self, toml_config: str) -> int:
        try:
            with self._lock:
                toml_bytes = toml_config.encode('utf-8')
                c_config = ctypes.c_char_p(toml_bytes)
                return self._lib.parse_config(c_config)
        except Exception as e:
            logger.exception(f"parse_config failed: {e}")
            return -1

    def _get_last_error(self) -> str:
        try:
            with self._lock:
                error_ptr = c_char_p()
                self._lib.get_error_msg(ctypes.byref(error_ptr))
            raw_ptr = ctypes.cast(error_ptr, c_void_p).value
            if raw_ptr:
                msg = ctypes.string_at(raw_ptr).decode('utf-8', errors='replace')
                if self._has_symbol('free_string'):
                    self._lib.free_string(raw_ptr)
                return msg
            return ""
        except Exception:
            return ""

    def _retain_instances(self, names: List[str]) -> None:
        try:
            with self._lock:
                if not names:
                    ret = self._lib.retain_network_instance(None, 0)
                else:
                    encoded = [n.encode('utf-8') for n in names]
                    arr = (c_char_p * len(names))(*encoded)
                    ret = self._lib.retain_network_instance(arr, len(names))
                if ret != 0:
                    raise RuntimeError(f"retain_network_instance failed: {self._get_last_error()}")
        except Exception as e:
            logger.exception(f"_retain_instances failed: {e}")
            raise

    def _list_all_instance_names(self) -> List[str]:
        info = self._collect_via_raw_ffi()
        return list(info.keys())

    def _collect_via_raw_ffi(self, max_len: int = _MAX_INSTANCE_COUNT) -> Dict[str, Any]:
        try:
            with self._lock:
                infos = (KeyValuePair * max_len)()
                count = self._lib.collect_network_infos(infos, max_len)
                if count < 0:
                    return {}
                result = {}
                for i in range(min(count, max_len)):
                    key_ptr = infos[i].key
                    val_ptr = infos[i].value
                    key = ctypes.string_at(key_ptr).decode('utf-8') if key_ptr else ""
                    value = ctypes.string_at(val_ptr).decode('utf-8') if val_ptr else ""
                    # logger.debug(f"collect_network_infos: key={key}, value={value}")
                    result[key] = json.loads(value) if value else {}
                    if self._has_symbol('free_string'):
                        if key_ptr:
                            self._lib.free_string(key_ptr)
                        if val_ptr:
                            self._lib.free_string(val_ptr)
                return result
        except Exception as e:
            logger.exception(f"_collect_via_raw_ffi failed: {e}")
        return {}

    def _addr_to_ipv4(self, addr: int) -> str:
        if not addr:
            return ""
        return ".".join(str((addr >> (i * 8)) & 0xFF) for i in range(3, -1, -1))

    def _latency_to_ms(self, latency_us: int) -> float:
        if isinstance(latency_us, str):
            latency_us = int(latency_us)
        if not latency_us or latency_us <= 0:
            return 0
        ms = latency_us / 1000
        return round(ms, 2)

    def _format_nat_type(self, nat_type: int) -> str:
        types = {
            0: "Unknown",
            1: "OpenInternet",
            2: "NoPAT",
            3: "FullCone",
            4: "Restricted",
            5: "PortRestricted",
            6: "Symmetric",
            7: "SymUdpFirewall",
        }
        if isinstance(nat_type, str):
            try:
                nat_type = int(nat_type)
            except ValueError:
                return nat_type
        return types.get(nat_type, "Unknown")

    def _format_cost(self, cost: int) -> str:
        if cost == 0:
            return "Local"
        if cost == 1:
            return "p2p"
        return f"relay{cost}"

    def _humanize_bytes(self, size: int, for_short: bool = False) -> str:
        """将字节数转为可读格式。

        for_short=False: 1.46 KB, 15.00 MB, 5.20 GB
        for_short=True:  1.46 K, 15 M, 5.20 G  （单位单字母，>=10 时省略小数）
        """
        if isinstance(size, str):
            size = int(size)
        # unit_names = ["B", "K", "M", "G", "T"] if for_short else ["B", "KB", "MB", "GB", "TB"]
        unit_names = ["B", "KB", "MB", "GB", "TB"]
        for unit in unit_names:
            if abs(size) < 1024:
                if for_short and size >= 10:
                    return f"{int(size)} {unit}"
                return f"{size:.2f} {unit}"
            size /= 1024
        # return f"{size:.2f} PB" if for_short else f"{size:.2f} P"
        return f"{size:.2f} PB"

    # def get_network_infos(self, max_length: int = 10) -> Dict[str, NetworkInstanceInfo]:
    #     raw = self._collect_via_raw_ffi(max_length)
    #     if not raw:
    #         return {}
    #
    #     result = {}
    #     for instance_name, json_data in raw.items():
    #         result[instance_name] = NetworkInstanceInfo.from_dict(json_data) if json_data else NetworkInstanceInfo()
    #     return result

    # def get_network_infos_raw(self, max_length: int = 10) -> Dict[str, Any]:
    #     return self._collect_via_raw_ffi(max_length)