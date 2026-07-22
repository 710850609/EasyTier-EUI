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
        """
        获取最后错误信息
        """
        if self._lib is None:
            return "FFI library not loaded"
        result = self._lib.get_error_msg()
        if result:
            return result.decode('utf-8', errors='replace')
        return ""

    def parse_config(self, toml_config: str) -> int:
        """
        解析 TOML 配置
        toml_config: 配置字符串
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            return self._lib.parse_config(toml_config.encode('utf-8'))
        except Exception as e:
            logger.exception(f"parse_config failed: {e}")
            return -1

    def run_network_instance(self, toml_config: str) -> int:
        """
        启动网络实例
        toml_config: 配置字符串
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            return self._lib.run_network_instance(toml_config.encode('utf-8'))
        except Exception as e:
            logger.exception(f"run_network_instance failed: {e}")
            return -1

    def retain_network_instance(self, instance_names: List[str]) -> int:
        """
        保留单个实例
        instance_names: 实例名
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            if not instance_names:
                return self._lib.retain_network_instance(None, 0)
            encoded = [name.encode('utf-8') for name in instance_names]
            arr = (c_char_p * len(encoded))(*encoded)
            return self._lib.retain_network_instance(arr, len(encoded))
        except Exception as e:
            logger.exception(f"retain_network_instance failed: {e}")
            return -1

    def stop_all_instances(self) -> int:
        """
        停止所有实例
        return: 0 成功，-1 失败
        """
        return self.retain_network_instance([])

    def delete_network_instance(self, instance_names: List[str]) -> int:
        """
        删除网络实例
        instance_names: 实例名
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            if not instance_names:
                return 0
            encoded = [name.encode('utf-8') for name in instance_names]
            arr = (c_char_p * len(encoded))(*encoded)
            return self._lib.delete_network_instance(arr, len(encoded))
        except Exception as e:
            logger.exception(f"delete_network_instance failed: {e}")
            return -1

    def collect_network_infos(self, max_length: int = 10) -> Dict[str, Any]:
        """
        收集网络实例信息
        max_length: 最大返回数量
        return: 信息字符串数组
        """
        if self._lib is None:
            return {}
        try:
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
        except Exception as e:
            logger.exception(f"collect_network_infos failed: {e}")
            return {}

    def list_instance(self, max_length: int = 10) -> Dict[str, str]:
        """
        收集网络信息为 Map
        max_length: 最大返回数量
        return: Map<String, String>
        """
        if self._lib is None:
            return {}
        try:
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
        except Exception as e:
            logger.exception(f"list_instance failed: {e}")
            return {}

    def collect_network_infos_json(self, max_length: int = 10) -> str:
        info = self.collect_network_infos(max_length)
        return json.dumps({"map": info})

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        """
        设置 TUN 文件描述符
        instance_name: 实例名
        fd: TUN 文件描述符
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            return self._lib.set_tun_fd(instance_name.encode('utf-8'), fd)
        except Exception as e:
            logger.exception(f"set_tun_fd failed: {e}")
            return -1

    def call_json_rpc(self, service_name: str, method_name: str,
                      payload_json: str, domain_name: str = None) -> Optional[str]:
        if self._lib is None:
            return None
        try:
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
        except Exception as e:
            logger.exception(f"call_json_rpc failed: {e}")
            return None

    def _cost_to_string(self, cost: int) -> str:
        if cost == 0:
            return 'Local'
        elif cost == 1:
            return 'p2p'
        else:
            return f'relay{cost - 1}'

    def _nat_type_to_string(self, nat_type: int) -> str:
        nat_types = {
            0: 'Unknown',
            1: 'FullCone',
            2: 'Restricted',
            3: 'PortRestricted',
            4: 'Symmetric',
            5: 'SymmetricEasyInc',
            6: 'SymmetricEasyDec',
            7: 'SymUdpFirewall',
            8: 'NoPAT',
            9: 'OpenInternet',
        }
        return nat_types.get(nat_type, 'Unknown')

    def _ipv4_addr_to_string(self, addr_obj) -> str:
        if not addr_obj:
            return ''
        address = addr_obj.get('address', {})
        addr = address.get('addr', 0)
        if not addr:
            return ''
        return f"{(addr >> 24) & 0xFF}.{(addr >> 16) & 0xFF}.{(addr >> 8) & 0xFF}.{addr & 0xFF}"

    def _ipv4_inet_to_string(self, inet_obj) -> str:
        if not inet_obj:
            return ''
        ip = self._ipv4_addr_to_string(inet_obj)
        if not ip:
            return ''
        network_length = inet_obj.get('network_length', 24)
        return f"{ip}/{network_length}"

    def get_version(self) -> str:
        try:
            info = self.collect_network_infos(1)
            if info:
                inst = next(iter(info.values()), {})
                if isinstance(inst, dict):
                    my_node = inst.get('my_node_info', {})
                    return my_node.get('version', 'unknown')
        except Exception as e:
            logger.exception(f"get_version failed: {e}")
        return 'unknown'

    def get_status(self) -> Optional[Dict[str, Any]]:
        try:
            info = self.collect_network_infos(1)
            if not info:
                return None
            inst = next(iter(info.values()), {})
            if isinstance(inst, dict):
                pairs = inst.get('peer_route_pairs', [])
                return {
                    'running': inst.get('running', False),
                    'peers_count': len(pairs),
                    'error_msg': inst.get('error_msg', ''),
                }
        except Exception as e:
            logger.exception(f"get_status failed: {e}")
        return None

    def get_peers(self) -> list:
        try:
            info = self.collect_network_infos(1)
            if not info:
                return []
            inst = next(iter(info.values()), {})
            if not isinstance(inst, dict):
                return []

            my_node = inst.get('my_node_info', {})
            my_stun = my_node.get('stun_info', {})
            my_nat_type = self._nat_type_to_string(my_stun.get('udp_nat_type', 0))
            my_version = my_node.get('version', '')
            my_hostname = my_node.get('hostname', '')
            my_ipv4 = self._ipv4_inet_to_string(my_node.get('virtual_ipv4'))

            peers = []
            pairs = inst.get('peer_route_pairs', [])
            for pair in pairs:
                route = pair.get('route', {})
                peer = pair.get('peer', {})

                peer_id = route.get('peer_id', 0)
                hostname = route.get('hostname', '')
                version = route.get('version', '')
                cost = self._cost_to_string(route.get('cost', 0))
                proxy_cidrs = route.get('proxy_cidrs', [])
                cidr = proxy_cidrs[0] if proxy_cidrs else ''
                ipv4 = self._ipv4_inet_to_string(route.get('ipv4_addr'))

                conns = peer.get('conns', [])
                conn = conns[0] if conns else {}
                stats = conn.get('stats', {})
                tunnel = conn.get('tunnel', {})

                lat_us = stats.get('latency_us', 0)
                if isinstance(lat_us, str):
                    try:
                        lat_us = int(lat_us)
                    except ValueError:
                        lat_us = 0
                lat_ms = max(1, lat_us // 1000) if lat_us else 0

                rx_bytes = stats.get('rx_bytes', 0)
                tx_bytes = stats.get('tx_bytes', 0)
                loss_rate = conn.get('loss_rate', 0)
                tunnel_proto = tunnel.get('tunnel_type', '')

                stun = route.get('stun_info', {})
                nat_type = self._nat_type_to_string(stun.get('udp_nat_type', 0))

                node_type = 'server' if hostname.startswith('PublicServer_') else 'normal'
                if node_type == 'server':
                    hostname = hostname.replace('PublicServer_', '')

                peers.append({
                    'id': peer_id,
                    'peer_id': peer_id,
                    'ipv4': ipv4,
                    'hostname': hostname,
                    'cost': cost,
                    'lat_ms': lat_ms,
                    'loss_rate': loss_rate,
                    'rx_bytes': rx_bytes,
                    'tx_bytes': tx_bytes,
                    'nat_type': nat_type,
                    'tunnel_proto': tunnel_proto,
                    'cidr': cidr,
                    'version': version,
                    'type': node_type,
                })

            if my_ipv4:
                peers.append({
                    'id': my_node.get('peer_id', 0),
                    'peer_id': my_node.get('peer_id', 0),
                    'ipv4': my_ipv4,
                    'hostname': my_hostname,
                    'cost': 'Local',
                    'lat_ms': 0,
                    'loss_rate': 0,
                    'rx_bytes': '-',
                    'tx_bytes': '-',
                    'nat_type': my_nat_type,
                    'tunnel_proto': '',
                    'cidr': my_ipv4,
                    'version': my_version,
                    'type': 'normal',
                })

            return peers
        except Exception as e:
            logger.exception(f"get_peers failed: {e}")
            return []


et_bridge = EasyTierFFI()