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
import re
import threading
from ctypes import c_char_p, c_int, c_void_p, POINTER, Structure, c_ulonglong
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# 缓存当前运行的实例名，避免调用 list_instance FFI（该 FFI 在 Android 上不安全）
_current_instance_name: Optional[str] = None

# 全局 FFI 调用锁：Rust 层不是线程安全的，必须串行化所有 FFI 调用
_ffi_lock = threading.RLock()  # RLock 可重入，get_last_error 在已持锁的 call_json_rpc 内调用时不会死锁


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
        获取最后错误信息（线程安全）
        """
        if self._lib is None:
            return "FFI library not loaded"
        with _ffi_lock:
            result = self._lib.get_error_msg()
        if result:
            return result.decode('utf-8', errors='replace')
        return ""

    def parse_config(self, toml_config: str) -> int:
        """
        解析 TOML 配置（线程安全）
        toml_config: 配置字符串
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            with _ffi_lock:
                return self._lib.parse_config(toml_config.encode('utf-8'))
        except Exception as e:
            logger.exception(f"parse_config failed: {e}")
            return -1

    def run_network_instance(self, toml_config: str) -> int:
        """
        启动网络实例（线程安全）
        toml_config: 配置字符串
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            # 从 TOML 配置中提取实例名，缓存到全局变量，避免后续调用 list_instance FFI
            global _current_instance_name
            import re
            match = re.search(r'^\s*instance_name\s*=\s*"([^"]+)"', toml_config, re.MULTILINE)
            if match:
                _current_instance_name = match.group(1)
            with _ffi_lock:
                ret = self._lib.run_network_instance(toml_config.encode('utf-8'))
                if ret == 0:
                    logger.info(f"Instance '{_current_instance_name}' started via FFI")
            return ret
        except Exception as e:
            logger.exception(f"run_network_instance failed: {e}")
            return -1

    def retain_network_instance(self, instance_names: List[str]) -> int:
        """
        保留单个实例（线程安全）
        instance_names: 实例名
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            with _ffi_lock:
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
        停止所有实例（线程安全）
        return: 0 成功，-1 失败
        """
        with _ffi_lock:
            global _current_instance_name
            _current_instance_name = None
            return self._lib.retain_network_instance(None, 0) if self._lib else -1

    def delete_network_instance(self, instance_names: List[str]) -> int:
        """
        删除网络实例（线程安全）
        instance_names: 实例名
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            with _ffi_lock:
                if not instance_names:
                    return 0
                global _current_instance_name
                _current_instance_name = None
                encoded = [name.encode('utf-8') for name in instance_names]
                arr = (c_char_p * len(encoded))(*encoded)
                return self._lib.delete_network_instance(arr, len(encoded))
        except Exception as e:
            logger.exception(f"delete_network_instance failed: {e}")
            return -1

    def _make_instance_selector(self, instance_name: str) -> Dict[str, Any]:
        return {
            "instance": {
                "instance_selector": {
                    "name": instance_name
                }
            }
        }

    def _list_peer_route_pair(self, peers: List[Dict], routes: List[Dict]) -> List[Dict]:
        pairs = []
        for route in routes:
            peer_id = route.get('peer_id', 0)
            peer = next((p for p in peers if p.get('peer_id') == peer_id), None)
            pairs.append({
                "route": route,
                "peer": peer,
            })

        def sort_key(pair):
            route = pair.get('route', {}) or {}
            feature_flag = route.get('feature_flag') or {}
            is_public = feature_flag.get('is_public_server', False)
            ipv4 = (route.get('ipv4_addr') or {}).get('address') or {}
            addr = ipv4.get('addr', 0)
            return (0 if is_public else 1, addr)

        pairs.sort(key=sort_key)
        return pairs

    def collect_network_infos_via_rpc(self, max_length: int = 10) -> Dict[str, Any]:
        """
        通过 RPC 调用收集网络实例信息（线程安全）
        替代 collect_network_infos FFI 调用，避免多 Tokio Runtime 冲突导致的崩溃
        使用缓存的实例名，避免调用 list_instance FFI（Android 上不安全）
        """
        global _current_instance_name
        if self._lib is None:
            return {}
        try:
            inst_name = _current_instance_name
            if not inst_name:
                logger.warning("collect_network_infos_via_rpc: no cached instance name, returning empty")
                return {}

            result = {}
            try:
                selector_json = json.dumps(self._make_instance_selector(inst_name))
                peer_service = "api.instance.PeerManageRpcService"
                vpn_service = "api.instance.VpnPortalRpcService"
                config_service = "api.config.ConfigRpcService"

                nodes = {}
                routes = []
                peers = []
                foreign_network_summary = []
                vpn_portal_cfg = None
                dev_name = ""

                list_peer_resp = self.call_json_rpc(peer_service, "ListPeer", selector_json)
                if list_peer_resp:
                    try:
                        resp_obj = json.loads(list_peer_resp)
                        peers = resp_obj.get('peer_infos', [])
                    except json.JSONDecodeError:
                        pass

                show_node_resp = self.call_json_rpc(peer_service, "ShowNodeInfo", selector_json)
                if show_node_resp:
                    try:
                        resp_obj = json.loads(show_node_resp)
                        node_info = resp_obj.get('node_info')
                        if node_info:
                            nodes = node_info
                    except json.JSONDecodeError:
                        pass

                list_route_resp = self.call_json_rpc(peer_service, "ListRoute", selector_json)
                if list_route_resp:
                    try:
                        resp_obj = json.loads(list_route_resp)
                        routes = resp_obj.get('routes', [])
                    except json.JSONDecodeError:
                        pass

                foreign_summary_resp = self.call_json_rpc(
                    peer_service, "GetForeignNetworkSummary", selector_json
                )
                if foreign_summary_resp:
                    try:
                        resp_obj = json.loads(foreign_summary_resp)
                        foreign_network_summary = resp_obj.get('summary', [])
                    except json.JSONDecodeError:
                        pass

                vpn_resp = self.call_json_rpc(vpn_service, "GetVpnPortalInfo", selector_json)
                if vpn_resp:
                    try:
                        resp_obj = json.loads(vpn_resp)
                        portal_info = resp_obj.get('vpn_portal_info')
                        if portal_info:
                            vpn_portal_cfg = portal_info.get('client_config')
                    except json.JSONDecodeError:
                        pass

                config_resp = self.call_json_rpc(config_service, "GetConfig", selector_json)
                if config_resp:
                    try:
                        resp_obj = json.loads(config_resp)
                        config = resp_obj.get('config')
                        if config:
                            dev_name = config.get('dev_name', '')
                    except json.JSONDecodeError:
                        pass

                if nodes:
                    nodes['vpn_portal_cfg'] = vpn_portal_cfg

                peer_route_pairs = self._list_peer_route_pair(peers, routes)

                running_info = {
                    "dev_name": dev_name,
                    "my_node_info": nodes if nodes else None,
                    "events": [],
                    "routes": routes,
                    "peers": peers,
                    "peer_route_pairs": peer_route_pairs,
                    "running": True,
                    "error_msg": None,
                    "foreign_network_summary": foreign_network_summary,
                }
                result[inst_name] = running_info

            except Exception as e:
                logger.exception(f"collect_network_infos_via_rpc: failed for instance {inst_name}: {e}")
                result[inst_name] = {
                    "running": False,
                    "error_msg": str(e),
                }

            return result
        except Exception as e:
            logger.exception(f"collect_network_infos_via_rpc failed: {e}")
            return {}

    def collect_network_infos(self, max_length: int = 10) -> Dict[str, Any]:
        """
        收集网络实例信息（线程安全）
        优先使用 RPC 方式，避免 collect_network_infos FFI 的多 Tokio Runtime 冲突
        """
        return self.collect_network_infos_via_rpc(max_length)

    def list_instance(self, max_length: int = 10) -> Dict[str, str]:
        """
        收集网络信息为 Map（线程安全）
        max_length: 最大返回数量
        return: Map<String, String>
        """
        if self._lib is None:
            return {}
        try:
            with _ffi_lock:
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
        设置 TUN 文件描述符（线程安全）
        instance_name: 实例名
        fd: TUN 文件描述符
        return: 0 成功，-1 失败
        """
        if self._lib is None:
            return -1
        try:
            with _ffi_lock:
                return self._lib.set_tun_fd(instance_name.encode('utf-8'), fd)
        except Exception as e:
            logger.exception(f"set_tun_fd failed: {e}")
            return -1

    def call_json_rpc(self, service_name: str, method_name: str,
                      payload_json: str, domain_name: str = None) -> Optional[str]:
        if self._lib is None:
            return None
        try:
            with _ffi_lock:
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

    def is_running(self, instance_name: str = None) -> bool:
        """
        检查是否有实例在运行（纯 Python，不调用 FFI，避免 Android 上崩溃）
        instance_name: 可选，指定实例名则检查该实例是否运行
        """
        if instance_name is not None:
            return _current_instance_name == instance_name
        return _current_instance_name is not None

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