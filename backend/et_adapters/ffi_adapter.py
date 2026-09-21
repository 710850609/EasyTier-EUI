#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FfiAdapter — current default FFI adapter for v2.4.5/v2.6.4/v2.7.0"""
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

from et_adapters.interface import IEasyTierAdapter
from . import et_util
from locales import get_last_lang
from utils import run_configs, app_settings

logger = logging.getLogger(__name__)
# github action 注入版本号，格式 2.6.4-8428a89d
_FFI_LIB_VERSION = "unknown"
_MAX_INSTANCE_COUNT = 20

def get_built_in_version() -> str:
    return _FFI_LIB_VERSION

def get_ffi_lib_name() -> str:
    if sys.platform == 'linux':
        return 'libeasytier_ffi.so'
    elif sys.platform == 'win32':
        return 'easytier_ffi.dll'
    else:
        return 'libeasytier_ffi.dylib'


def set_ffi_version(et_version):
    """设置FFI版本"""
    if et_version is None:
        app_settings.save('ffi_version', None)
        logger.info("FFI version set to None")
        return
    et_version: Optional[str] = et_version.replace('v', '') if et_version else None
    if not et_version:
        logger.warning("no FFI version value")
        return
    app_settings.save('ffi_version', et_version)

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
        lib_name = get_ffi_lib_name()
        lib_path = os.path.join(run_configs.core_dir(), lib_name)
        if os.path.exists(lib_path) and os.path.getsize(lib_path) > 0:
            logger.info(f"Using FFI By Path: {lib_path}")
            lib_name = lib_path
        self._lib = ctypes.CDLL(lib_name)
        self._setup_functions()
        logger.info(f"Loaded EasyTier FFI: {lib_name}")
        self._lock = threading.RLock()
        self._instance_set: Set[str] = set()
        self._routes_config: Dict[str, List[str]] = {}
        self._start_times: Dict[str, float] = {}
        self._ffi_cache: Dict[str, Any] = {}
        self._ffi_cache_time: float = 0.0
        self._FFI_CACHE_TTL = 1.0
        self._enable_magic_dns_set: Set[str] = set()
        self._mtu_config: Dict[str, int] = {}
        self._enable_cache = run_configs.IS_ANDROID
        self._monitor_threads: Dict[str, threading.Thread] = {}
        self._monitor_states: Dict[str, bool] = {}

    def _invalidate_ffi_cache(self):
        self._ffi_cache = {}
        self._ffi_cache_time = 0.0

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
        # v2.7.0 新增的 FFI 符号（可选）
        if self._has_symbol('call_json_rpc'):
            lib.call_json_rpc.argtypes = [c_char_p, c_char_p, c_char_p, c_char_p, POINTER(c_char_p)]
            lib.call_json_rpc.restype = c_int
        if self._has_symbol('start_config_server_client'):
            lib.start_config_server_client.argtypes = [c_char_p, c_char_p, c_char_p, c_int, c_void_p, c_void_p]
            lib.start_config_server_client.restype = c_int
        if self._has_symbol('stop_config_server_client'):
            lib.stop_config_server_client.argtypes = []
            lib.stop_config_server_client.restype = c_int
        if self._has_symbol('is_config_server_client_connected'):
            lib.is_config_server_client_connected.argtypes = []
            lib.is_config_server_client_connected.restype = c_int

    # ─────────────────── ffi 接口 开始 ─────────────────────────────

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
        now = time.time()
        if self._enable_cache and self._ffi_cache and (now - self._ffi_cache_time) < self._FFI_CACHE_TTL:
            return self._ffi_cache
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
                if self._enable_cache:
                    self._ffi_cache = result
                    self._ffi_cache_time = now
                return result
        except Exception as e:
            logger.exception(f"_collect_via_raw_ffi failed: {e}")
        return {}

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

    def _call_json_rpc(self, service_name: str, method_name: str, domain_name: str, payload_json: str) -> str:
        """调用 EasyTier 暴露的 RPC 服务（protobuf JSON 格式）。

        v2.7.0 开始支持。

        注意：api.logger.LoggerRpcService 在 FFI 模式下不可用（核心日志未初始化），
        其他 RPC 服务（如实例查询、节点管理等）均可正常调用。

        :param service_name: RPC 服务名，如 "api.manage.NetworkInstanceService"
        :param method_name:  RPC 方法名，如 "list_instances"
        :param domain_name:  域名称，可选（传空字符串表示无域筛选）
        :param payload_json: JSON 格式的请求参数，如 '{"instance_name": "default"}'
        :return: JSON 格式的响应字符串；失败时抛出 RuntimeError
        :rtype: str
        """
        if not self._has_symbol('call_json_rpc'):
            raise RuntimeError("call_json_rpc symbol not available (requires EasyTier >= v2.7.0)")
        try:
            with self._lock:
                svc = ctypes.c_char_p(service_name.encode('utf-8'))
                mtd = ctypes.c_char_p(method_name.encode('utf-8'))
                dom = ctypes.c_char_p(domain_name.encode('utf-8') if domain_name else b'')
                pld = ctypes.c_char_p(payload_json.encode('utf-8'))
                resp_ptr = ctypes.c_char_p()
                ret = self._lib.call_json_rpc(svc, mtd, dom, pld, ctypes.byref(resp_ptr))
                if ret != 0:
                    raise RuntimeError(f"call_json_rpc failed: {self._get_last_error()}")
                raw_ptr = ctypes.cast(resp_ptr, c_void_p).value
                if raw_ptr:
                    result = ctypes.string_at(raw_ptr).decode('utf-8', errors='replace')
                    if self._has_symbol('free_string'):
                        self._lib.free_string(raw_ptr)
                    return result
                return ''
        except RuntimeError as e:
            logger.exception(f"call_json_rpc runtime error: {e}")
            raise
        except Exception as e:
            raise RuntimeError(f"call_json_rpc failed: {e}") from e

    def _start_config_server_client(self, config_server_url: str, hostname: str,
                                   machine_id: str, secure_mode: bool) -> None:
        """启动托管的配置服务器客户端。

        v2.7.0 开始支持。

        启动后，FFI 层会通过配置服务器同步远程实例配置，并根据事件自动创建/删除
        本地网络实例。配置服务器客户端与 FFI 数据平面互斥，数据平面运行时调用此
        方法会返回 -1。

        :param config_server_url: 配置服务器地址，如 "https://config.example.com"
        :param hostname:          主机名，可传空字符串
        :param machine_id:        机器标识 ID
        :param secure_mode:       是否启用安全模式
        :raises RuntimeError: 符号不存在或调用失败时抛出
        """
        logger.info(f"start_config_server_client url={config_server_url} hostname={hostname}")
        if not self._has_symbol('start_config_server_client'):
            raise RuntimeError("start_config_server_client symbol not available (requires EasyTier >= v2.7.0)")
        try:
            with self._lock:
                url = ctypes.c_char_p(config_server_url.encode('utf-8'))
                host = ctypes.c_char_p(hostname.encode('utf-8') if hostname else None)
                mid = ctypes.c_char_p(machine_id.encode('utf-8'))
                sec = 1 if secure_mode else 0
                ret = self._lib.start_config_server_client(url, host, mid, sec, None, None)
                if ret != 0:
                    raise RuntimeError(f"start_config_server_client failed: {self._get_last_error()}")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"start_config_server_client failed: {e}") from e

    def _stop_config_server_client(self) -> None:
        """停止托管的配置服务器客户端。

        v2.7.0 开始支持。

        停止客户端，移除由配置服务器追踪的远程实例，等待进行中的回调完成，
        并释放配置服务器/数据平面互斥状态。

        :raises RuntimeError: 符号不存在或调用失败时抛出
        """
        logger.info("stop_config_server_client")
        if not self._has_symbol('stop_config_server_client'):
            raise RuntimeError("stop_config_server_client symbol not available (requires EasyTier >= v2.7.0)")
        try:
            with self._lock:
                ret = self._lib.stop_config_server_client()
                if ret != 0:
                    raise RuntimeError(f"stop_config_server_client failed: {self._get_last_error()}")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"stop_config_server_client failed: {e}") from e

    def _is_config_server_client_connected(self) -> bool:
        """查询配置服务器客户端是否已连接。

        v2.7.0 开始支持。

        :return: 客户端存在且报告已连接时返回 True，否则返回 False
        :rtype: bool
        :raises RuntimeError: 当 FFI 符号不可用时抛出
        """
        if not self._has_symbol('is_config_server_client_connected'):
            raise RuntimeError("is_config_server_client_connected symbol not available (requires EasyTier >= v2.7.0)")
        try:
            with self._lock:
                return self._lib.is_config_server_client_connected() != 0
        except Exception as e:
            logger.exception(f"is_config_server_client_connected exception: {e}")
            return False

    # ─────────────────── ffi 接口 结束 ─────────────────────────────

    def get_version(self) -> str:
        ffi_version: str = app_settings.get('ffi_version')
        if ffi_version:
            return ffi_version
        else:
            return _FFI_LIB_VERSION

    def start_network(self, toml_path: str, instance_name: str) -> None:
        logger.info(f"start_network {instance_name}")
        try:
            with open(toml_path, 'r', encoding='utf-8') as f:
                toml_config = f.read()
            doc = tomlkit.parse(toml_config)
            rebuild_toml = False
            # flags = doc.get('flags', {})
            # if 'compression' in flags:
            #     compression = flags['compression']
            #     if compression:
            #         flags['data_compress_algo'] = compression.capitalize()
            #     del flags['compression']
            #     doc['flags'] = flags
            #     rebuild_toml = True
            # 避免外部修改配置文件名，导致启动后，找不到组网节点数据
            if doc['instance_name'] != instance_name:
                logger.warning(f"配置中的instance_name参数和实际指定值不一致，已覆盖为指定值【{instance_name}】")
                doc['instance_name'] = instance_name
                rebuild_toml = True
            # 自适应 mtu 。根据AI识别：ffi模式下，没根据是否加密自适应 mtu
            mtu = doc.get('flags', {}).get('mtu')
            if run_configs.IS_ANDROID:
                if mtu is None:
                    # 参考官方安卓实现，默认 1300
                    mtu = 1300
                    rebuild_toml =True
                # 安卓系统下，如果hostname为空，使用设备名称
                hostname = doc.get('hostname')
                if not hostname:
                    try:
                        from java import jclass
                        MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
                        manager = MainActivity.getEasyTierManager()
                        if manager is not None:
                            doc['hostname'] = manager.getDeviceName()
                        rebuild_toml = True
                        logger.info(f"安卓设备名称为空，已使用设备名称替代: {doc['hostname']}")
                    except Exception as e:
                        logger.warning(f"获取安卓设备名称失败: {e}")

            if mtu is None:
                if doc.get('flags', {}).get('enable_encryption'):
                    mtu = 1360
                else:
                    mtu = 1380
                rebuild_toml =True
            if rebuild_toml:
                toml_config = tomlkit.dumps(doc)
                logger.info(f"Rebuilt toml config for run_network_instance: \n{toml_config}")
            self._routes_config[instance_name] = [str(r) for r in (doc.get('routes') or [])]
            ret = self._parse_config(toml_config)
            if ret != 0:
                raise RuntimeError(f"Config parse failed: {self._get_last_error()}")
            if run_configs.IS_ANDROID:
                while len(self._instance_set) > 0:
                    # 安卓环境下，确保所有实例都停止，再启动新实例
                    self.stop_network(self._instance_set.pop())
            with self._lock:
                toml_bytes = toml_config.encode('utf-8')
                c_config = ctypes.c_char_p(toml_bytes)
                ret = self._lib.run_network_instance(c_config)
                if ret != 0:
                    raise RuntimeError(f"run_network_instance failed: {self._get_last_error()}")
            self._instance_set.add(instance_name)
            # 记录是否开启了魔法DNS
            accept_dns = doc.get('flags', {}).get('accept_dns')
            if accept_dns:
                self._enable_magic_dns_set.add(instance_name)
            # 参考 官方安卓 实现，但没参考官方 1500 默认值
            self._mtu_config[instance_name] = mtu
            self._invalidate_ffi_cache()
            logger.info(f"Instance '{instance_name}' started via FFI")
            time.sleep(2.0)
            self._start_monitor(instance_name)
        except Exception as e:
            logger.exception(f"start_network failed: {e}")
            raise

    def stop_network(self, instance_name: str) -> None:
        logger.info(f"stop_network {instance_name}")
        self._stop_monitor(instance_name)
        all_instances = self._list_all_instance_names()
        keep = [n for n in all_instances if n != instance_name]
        self._retain_instances(keep)
        if instance_name in self._instance_set:
            self._instance_set.remove(instance_name)
        if instance_name in self._enable_magic_dns_set:
            self._enable_magic_dns_set.remove(instance_name)
        self._mtu_config.pop(instance_name, None)
        self._routes_config.pop(instance_name, None)
        self._start_times.pop(instance_name, None)
        self._invalidate_ffi_cache()

        # 停止 Android VPN 监控和服务
        try:
            if run_configs.IS_ANDROID:
                from java import jclass
                MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
                manager = MainActivity.getEasyTierManager()
                if manager is not None:
                    manager.stopVpn()
        except Exception as e:
            logger.exception(f"fail to stop vpn manager monitor: {e}")

    def status(self, instance_name: str) -> bool:
        return instance_name in self._instance_set

    def get_peers(self, instance_name: str, relay_path: bool = False, proxy_info: bool = True) -> list[dict]:
        raw = self._collect_via_raw_ffi()
        instance_infos = raw.get(instance_name, {})
        peers = []
        my_node_info = instance_infos.get('my_node_info', {})
        if my_node_info:
            ipv4_addr = my_node_info.get('virtual_ipv4') or {}
            addr = (ipv4_addr.get('address') or {}).get('addr', 0)
            ipv4 = et_util.addr_to_ipv4(addr)
            network_len = ipv4_addr.get('network_length') or ''
            cidr = f"{ipv4}/{network_len}" if ipv4 else ''
            stun = my_node_info.get('stun_info', {})
            peers.append({
                'ipv4': ipv4,
                'cidr': cidr,
                'hostname': my_node_info.get('hostname') or '',
                'version': my_node_info.get('version') or '',
                'cost': 'Local',
                'tunnel_proto': '-',
                'lat_ms': '-',
                'loss_rate': '-',
                'rx_bytes': '-',
                'tx_bytes': '-',
                'nat_type': et_util.format_nat_type(stun.get('udp_nat_type', 0)),
                'id': str(my_node_info.get('peer_id', '')),
            })

        seen = set()
        peer_route_map = {}
        for pair in instance_infos.get('peer_route_pairs', []):
            route = pair.get('route') or {}
            peer = pair.get('peer') or {}
            if not route:
                continue
            pid = peer.get('peer_id') or route.get('peer_id')
            if pid is None:
                continue
            peer_route_map[pid] = (pair, peer, route)

        for pid, (pair, peer, route) in peer_route_map.items():
            if pid in seen:
                continue
            seen.add(pid)
            ipv4_addr = route.get('ipv4_addr') or {}
            ipv4 = et_util.addr_to_ipv4(ipv4_addr.get('address', {}).get('addr', 0))
            cidr = f"{ipv4}/{ipv4_addr.get('network_length', '')}" if ipv4 else ''
            stun = route.get('stun_info') or {}
            cost = route.get('cost', 0)

            peer_uri = None
            if route.get('feature_flag', {}).get('is_public_server', False):
                conns = peer.get('conns', [])
                if len(conns) > 0:
                    peer_uri = conns[0].get('tunnel', {}).get('remote_addr', {}).get('url', {})

            if cost == 1:
                lat_ms = et_util.get_latency_ms(peer)
            else:
                lat_first = route.get('path_latency_latency_first')
                lat_ms = f'{float(lat_first):.2f}' if lat_first is not None else '-'

            has_peer = bool(pair.get('peer'))

            relay = None
            if relay_path and cost > 1:
                relay = []
                cur_pid = pid
                while cur_pid is not None and len(relay) < cost:
                    entry = peer_route_map.get(cur_pid)
                    if not entry:
                        break
                    _, cur_peer_info, cur_route = entry
                    next_hop = cur_route.get('next_hop_peer_id')
                    is_first_hop = cur_route.get('cost', 0) == 1
                    cur_ipv4_inet = cur_route.get('ipv4_addr')
                    relay.append({
                        'peer_id': str(cur_route.get('peer_id', '')),
                        'hostname': cur_route.get('hostname', ''),
                        'ipv4': et_util.addr_to_ipv4(
                            cur_ipv4_inet.get('address', {}).get('addr', 0) if cur_ipv4_inet else 0
                        ),
                        'remote_addrs': et_util.get_remote_addrs(cur_peer_info),
                        'lat_ms': et_util.get_latency_ms(cur_peer_info)
                        if is_first_hop else None,
                    })
                    if next_hop == cur_pid or next_hop is None:
                        break
                    cur_pid = next_hop
                relay.reverse()
                relay = relay[:1]

            peers.append({
                'ipv4': ipv4,
                'cidr': cidr,
                'hostname': route.get('hostname') or '',
                'version': route.get('version') or '',
                'cost': et_util.format_cost(cost),
                'tunnel_proto': et_util.get_conn_protos(peer) if has_peer else '',
                'lat_ms': lat_ms,
                'loss_rate': et_util.get_loss_rate(peer) if has_peer else '0.0%',
                'rx_bytes': et_util.get_rx_bytes(peer) if has_peer else '0 B',
                'tx_bytes': et_util.get_tx_bytes(peer) if has_peer else '0 B',
                'nat_type': et_util.format_nat_type(stun.get('udp_nat_type', 0)),
                'id': str(route.get('peer_id', '')),
                'relay_path': relay,
                'proxy_cidrs': list(route.get('proxy_cidrs') or []),
                'proxy_info': [],
                'peer_uri': peer_uri,
            })

        peers.sort(key=lambda x: (
            0 if x['cost'] == 'Local' else 1,
            x['ipv4'] if x['ipv4'] else '255.255.255.255',
        ))
        return peers

    def check_peers(self, peer_uris: list[str], max_wait_second: int = 6) -> dict:
        """通过 FFI 启动临时网络实例来检测公开节点连通性"""
        import random
        import string as _string

        random_name = '_peer_check_' + ''.join(
            random.choices(_string.ascii_letters + _string.digits, k=8)
        )

        peers_toml = '\n'.join([f'[[peer]]\nuri = "{uri}"' for uri in peer_uris])
        toml_config = (
            f'instance_name = "{random_name}"\n'
            f'network_name = "{random_name}"\n'
            f'network_secret = "{random_name}"\n'
            f'no_listener = true\n'
            f'private_mode = true\n'
            f'{peers_toml}\n'
        )

        ret = self._parse_config(toml_config)
        if ret != 0:
            logger.warning(f"check_peers: parse_config failed for temp instance {random_name}")
            return {'success': {}, 'fail': list(peer_uris)}

        try:
            with self._lock:
                toml_bytes = toml_config.encode('utf-8')
                c_config = ctypes.c_char_p(toml_bytes)
                ret = self._lib.run_network_instance(c_config)
                if ret != 0:
                    logger.warning(f"check_peers: run_network_instance failed for temp instance {random_name}")
                    return {'success': {}, 'fail': list(peer_uris)}

            self._invalidate_ffi_cache()

            success = {}
            fail = list(peer_uris)
            start_time = time.time()

            while (time.time() - start_time) < max_wait_second:
                time.sleep(3)
                raw = self._collect_via_raw_ffi()
                inst_info = raw.get(random_name, {})
                peer_route_pairs = inst_info.get('peer_route_pairs', [])

                for pair in peer_route_pairs:
                    route = pair.get('route') or {}
                    peer = pair.get('peer') or {}
                    conns = peer.get('conns', [])
                    if not conns:
                        continue
                    tunnel = conns[0].get('tunnel') or {}
                    remote_addr = tunnel.get('remote_addr') or {}
                    uri = remote_addr.get('url', '')
                    if uri in fail:
                        fail.remove(uri)
                        stats = conns[0].get('stats') or {}
                        latency_us = float(stats.get('latency_us', 0))
                        success[uri] = {
                            'latency': max(1, latency_us // 1000),
                            'hostname': route.get('hostname', ''),
                            'relay': route.get('feature_flag', {}).get(
                                'avoid_relay_data', True
                            ) == False,
                        }

                if len(fail) == 0:
                    break

            return {'success': success, 'fail': fail}

        finally:
            all_names = self._list_all_instance_names()
            keep = [n for n in all_names if n != random_name]
            self._retain_instances(keep)
            self._invalidate_ffi_cache()

    def change_log_level(self, log_level: str, **kwargs) -> None:
        """
        FFI 模式不支持改变日志级别
        """
        pass

    def get_logs(self, params: dict) -> dict:
        raw = self._collect_via_raw_ffi()
        events = []
        for instance_name, info in raw.items():
            inst_events = info.get('events', []) or []
            for item in inst_events:
                item = json.loads(item)
                msg = f"{item.get('time', '')[11:22]}"
                for e_key, e_value in item.get('event', {}).items():
                    msg += f' {e_key} {str(e_value)}'
                events.insert(0, msg)
        return {
            'lines': '\n'.join(events) + ('\n' if events else ''),
            'offset': 0,
            'appending': False
        }


    def _get_route_info_dict(self, instance_name: str) -> Dict[str, Any]:
        info = {
            'virtual_ipv4': '',
            'virtual_ipv6': 'fd00::1/128',
            'dns_servers': [],
            'routes': [],
            'total_upload': '',
            'total_download': '',
            'mtu': self._mtu_config.get(instance_name),
        }
        total_upload = 0
        total_download = 0
        raw = self._collect_via_raw_ffi()
        if not raw:
            return info
        instance_infos = raw.get(instance_name, {})
        my_node_info = instance_infos.get('my_node_info', {})
        virtual_ipv4 = my_node_info.get('virtual_ipv4') or {}
        addr = (virtual_ipv4.get('address') or {}).get('addr', 0)
        addr_str = et_util.addr_to_ipv4(addr)
        network_len = virtual_ipv4.get('network_length') or '24'
        info['virtual_ipv4'] = f"{addr_str}/{network_len}" if addr_str else ""
        routes = instance_infos.get('routes') or []
        for route in routes:
            cidrs = route.get('proxy_cidrs') or []
            for cidr in cidrs:
                if '/' not in cidr:
                    cidr += '/32'
                info['routes'].append(cidr)
        manual_routes = self._routes_config.get(instance_name, [])
        for r in manual_routes:
            if r not in info['routes']:
                info['routes'].append(r)
        if instance_name in self._enable_magic_dns_set:
            magic_dns = "100.100.100.101"
            info['dns_servers'].append(magic_dns)
            info['routes'].append(f"{magic_dns}/32")
        for peer in (instance_infos.get('peers') or []):
            for conn in (peer.get('conns') or []):
                stats = conn.get('stats') or {}
                total_download += float(stats.get('rx_bytes', 0))
                total_upload += float(stats.get('tx_bytes', 0))
        info['total_upload'] = et_util.humanize_bytes(total_upload, for_short=True)
        info['total_download'] = et_util.humanize_bytes(total_download, for_short=True)
        return info

    def _start_monitor(self, instance_name: str):
        """
        监控线程
        """
        if not run_configs.IS_ANDROID:
            logger.info(f"Monitor not started for {instance_name} on Android platform")
            return
        if self._monitor_states.get(instance_name):
            logger.warning(f"Monitor already running for {instance_name}")
            return
        self._monitor_states[instance_name] = True
        t = threading.Thread(
            target=self._monitor_loop,
            args=(instance_name,),
            name=f"EasyTierMonitor-{instance_name}",
            daemon=True,
        )
        self._monitor_threads[instance_name] = t
        t.start()
        logger.info(f"Monitor started for {instance_name}")

    def _stop_monitor(self, instance_name: str):
        if not self._monitor_states.get(instance_name):
            return
        logger.info(f"Stopping monitor for {instance_name}")
        self._monitor_states[instance_name] = False
        t = self._monitor_threads.pop(instance_name, None)
        if t and t.is_alive():
            t.join(timeout=2.0)
            if t.is_alive():
                logger.warning(f"Monitor thread for {instance_name} did not stop in time")

    def _monitor_loop(self, instance_name: str):
        logger.info(f"Monitor loop started for {instance_name}")
        cached_state: Dict[str, Any] = {}
        last_notify_time = 0.0
        compare_keys = ['virtual_ipv4', 'virtual_ipv6', 'routes', 'dns_servers']

        while self._monitor_states.get(instance_name, False):
            try:
                info = self._get_route_info_dict(instance_name)
                if not info or not info.get('virtual_ipv4'):
                    time.sleep(2.5)
                    continue

                changed = any(info.get(k) != cached_state.get(k) for k in compare_keys)

                if changed or not cached_state:
                    cached_state = {k: info.get(k) for k in compare_keys}
                    self._start_times[instance_name] = time.time()
                    self._notify_kotlin_restart_vpn(instance_name, info)
                    last_notify_time = 0.0

                now = time.time()
                if now - last_notify_time >= 60.0:
                    last_notify_time = now
                    self._notify_kotlin_update_notification(instance_name, info)

                time.sleep(5.0)

            except Exception as e:
                logger.exception(f"Monitor loop error for {instance_name}: {e}")

        logger.info(f"Monitor loop ended for {instance_name}")

    def _notify_kotlin_restart_vpn(self, instance_name: str, info: Dict[str, Any]):
        try:
            if not run_configs.IS_ANDROID:
                return
            from java import jclass
            MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
            manager = MainActivity.getEasyTierManager()
            if manager is not None:
                ipv4 = info.get('virtual_ipv4', '')
                ipv6 = info.get('virtual_ipv6', '')
                cidrs = info.get('routes', [])
                dns = info.get('dns_servers', [])
                title, text = self._build_notification_text(instance_name, info)
                mtu = info.get('mtu') or 1400
                manager.stopVpn()
                manager.startVpn(ipv4, ipv6, cidrs, dns, title, text, mtu, instance_name)
                logger.info(f"Notified Kotlin: startVpn for {instance_name} ipv4={ipv4} ipv6={ipv6}")
        except Exception as e:
            logger.exception(f"Failed to notify Kotlin restartVpn: {e}")

    def _notify_kotlin_update_notification(self, instance_name: str, info: Dict[str, Any]):
        try:
            if not run_configs.IS_ANDROID:
                return
            from java import jclass
            MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
            manager = MainActivity.getEasyTierManager()
            if manager is not None:
                title, text = self._build_notification_text(instance_name, info)
                manager.updateNotification(title, text)
        except Exception as e:
            logger.exception(f"Failed to update notification: {e}")

    def _build_notification_text(self, instance_name: str, info: Dict[str, Any]) -> tuple:
        i18n = get_last_lang()
        is_chinese = i18n.startswith('zh')
        name = instance_name.replace('.toml', '')
        title = f"易组网 - {name} 运行中" if is_chinese else f"EasyTier-EUI - {name} Running"

        upload = info.get('total_upload', '')
        download = info.get('total_download', '')

        if not upload and not download:
            text = "连接中..." if is_chinese else "Connecting..."
            return title, text

        parts = []
        if upload:
            parts.append(f"↑{upload}")
        if download:
            parts.append(f"↓{download}")
        start_time = self._start_times.get(instance_name)
        uptime_seconds = int(time.time() - start_time) if start_time else 0
        parts.append("🕓")
        parts.append(self._format_uptime(uptime_seconds, is_chinese))
        text = "  ".join(parts)
        return title, text

    def _format_uptime(self, seconds: int, is_chinese: bool) -> str:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        if is_chinese:
            parts = []
            if days > 0:
                parts.append(f"{days}天")
            if hours > 0:
                parts.append(f"{hours}时")
            parts.append(f"{minutes}分")
            return "".join(parts)
        else:
            parts = []
            if days > 0:
                parts.append(f"{days}d ")
            if hours > 0:
                parts.append(f"{hours}h ")
            parts.append(f"{minutes}m")
            return "".join(parts)