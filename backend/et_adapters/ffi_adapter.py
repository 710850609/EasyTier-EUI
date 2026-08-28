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

from et_adapters.interface import IEasyTierAdapter
from locales import get_last_lang
from utils import run_configs, app_settings

logger = logging.getLogger(__name__)
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
            # flags = doc.get('flags', {})
            # rebuild_toml = False
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
            if mtu is None:
                if doc.get('flags', {}).get('enable_encryption'):
                    mtu = 1360
                else:
                    mtu = 1380
                rebuild_toml =True
            if run_configs.IS_ANDROID:
                # 参考官方安卓实现，固定 1300
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

    def get_peers(self, instance_name: str, relay_path: bool = False) -> list[dict]:
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
                'nat_type': self._format_nat_type(stun.get('udp_nat_type', 0)),
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
            ipv4 = self._addr_to_ipv4(ipv4_addr.get('address', {}).get('addr', 0))
            cidr = f"{ipv4}/{ipv4_addr.get('network_length', '')}" if ipv4 else ''
            stun = route.get('stun_info') or {}
            cost = route.get('cost', 0)

            if cost == 1:
                lat_ms = self._get_latency_ms(peer)
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
                        'ipv4': self._addr_to_ipv4(
                            cur_ipv4_inet.get('address', {}).get('addr', 0) if cur_ipv4_inet else 0
                        ),
                        'remote_addrs': self._get_remote_addrs(cur_peer_info),
                        'lat_ms': self._get_latency_ms(cur_peer_info)
                        if is_first_hop else None,
                    })
                    if next_hop == cur_pid or next_hop is None:
                        break
                    cur_pid = next_hop
                relay.reverse()

            peers.append({
                'ipv4': ipv4,
                'cidr': cidr,
                'hostname': route.get('hostname') or '',
                'version': route.get('version') or '',
                'cost': self._format_cost(cost),
                'tunnel_proto': self._get_conn_protos(peer) if has_peer else '',
                'lat_ms': lat_ms,
                'loss_rate': self._get_loss_rate(peer) if has_peer else '0.0%',
                'rx_bytes': self._get_rx_bytes(peer) if has_peer else '0 B',
                'tx_bytes': self._get_tx_bytes(peer) if has_peer else '0 B',
                'nat_type': self._format_nat_type(stun.get('udp_nat_type', 0)),
                'id': str(route.get('peer_id', '')),
                'relay': relay,
            })

        peers.sort(key=lambda x: (
            0 if x['cost'] == 'Local' else 1,
            x['ipv4'] if x['ipv4'] else '255.255.255.255',
        ))
        return peers


    def change_log_level(self, log_level: str, **kwargs) -> None:
        """
        FFI 模式不支持改变日志级别
        """
        pass

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
        addr_str = self._addr_to_ipv4(addr)
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
                total_download += stats.get('rx_bytes', 0)
                total_upload += stats.get('tx_bytes', 0)
        info['total_upload'] = self._humanize_bytes(total_upload, for_short=True)
        info['total_download'] = self._humanize_bytes(total_download, for_short=True)
        return info

    # ── 监控线程 ──────────────────────────────────────────────

    def _start_monitor(self, instance_name: str):
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

    def _format_tunnel_type(self, tunnel: dict) -> str:
        tunnel_type = tunnel.get('tunnel_type', '')
        if not tunnel_type:
            return ''
        if self._is_ipv6_tunnel(tunnel_type, tunnel):
            if tunnel_type.endswith('6'):
                return tunnel_type
            return tunnel_type + '6'
        return tunnel_type

    def _is_ipv6_tunnel(self, tunnel_type: str, tunnel: dict) -> bool:
        if '://' in tunnel_type:
            _, rest = tunnel_type.split('://', 1)
            if rest.startswith('['):
                return True
        for addr_key in ('resolved_remote_addr', 'local_addr', 'remote_addr'):
            addr = tunnel.get(addr_key, {})
            url = addr.get('url', '') if isinstance(addr, dict) else ''
            if url and '://[' in url:
                return True
        return False

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
            8: "SymEasyInc",
            9: "SymEasyDec",
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
        return f"relay({cost})"

    def _get_latency_ms(self, peer_info: dict) -> str:
        conns = peer_info.get('conns', [])
        default_conn_id = peer_info.get('default_conn_id', '')
        best = None
        for conn in conns:
            stats = conn.get('stats')
            if not stats:
                continue
            if default_conn_id and conn.get('conn_id', '') == default_conn_id:
                return f'{stats.get("latency_us", 0) / 1000.0:.2f}'
            lat = stats.get('latency_us', 0)
            if best is None or lat < best:
                best = lat
        if best is not None:
            return f'{best / 1000.0:.2f}'
        return '-'

    def _get_loss_rate(self, peer_info: dict) -> str:
        default_conn_id = peer_info.get('default_conn_id', '')
        best = None
        for conn in peer_info.get('conns', []):
            lr = conn.get('loss_rate', 0.0)
            if default_conn_id and conn.get('conn_id', '') == default_conn_id:
                return f'{lr * 100.0:.1f}%'
            if best is None:
                best = lr
        if best is not None:
            return f'{best * 100.0:.1f}%'
        return '-'

    def _get_rx_bytes(self, peer_info: dict) -> str:
        total = 0
        for conn in peer_info.get('conns', []):
            stats = conn.get('stats')
            if stats:
                total += stats.get('rx_bytes', 0)
        return self._humanize_bytes(total) if total else '-'

    def _get_tx_bytes(self, peer_info: dict) -> str:
        total = 0
        for conn in peer_info.get('conns', []):
            stats = conn.get('stats')
            if stats:
                total += stats.get('tx_bytes', 0)
        return self._humanize_bytes(total) if total else '-'

    def _get_conn_protos(self, peer_info: dict) -> str:
        protos = []
        for conn in peer_info.get('conns', []):
            tunnel = conn.get('tunnel')
            if not tunnel:
                continue
            tt = self._format_tunnel_type(tunnel)
            if tt and tt not in protos:
                protos.append(tt)
        return ','.join(protos) if protos else '-'

    def _get_remote_addrs(self, peer_info: dict) -> list[str]:
        addrs = []
        for conn in peer_info.get('conns', []):
            tunnel = conn.get('tunnel')
            if not tunnel:
                continue
            url = tunnel.get('resolved_remote_addr', {}).get('url', '') \
                or tunnel.get('remote_addr', {}).get('url', '')
            if url and url not in addrs:
                addrs.append(url)
        return addrs

    def _humanize_bytes(self, size: int, for_short: bool = False) -> str:
        """将字节数转为可读格式。

        for_short=False: 1.46 KB, 15.00 MB, 5.20 GB
        for_short=True:  1.46 K, 15 M, 5.20 G  （单位单字母，>=10 时省略小数）
        """
        if isinstance(size, str):
            size = int(size)
        unit_names = ["B", "KB", "MB", "GB", "TB"]
        for unit in unit_names:
            if abs(size) < 1024:
                if for_short and size >= 10:
                    return f"{int(size)} {unit}"
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"