#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CoreCliAdapter — CLI subprocess adapter for EasyTier Core"""
import ipaddress
import json
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import Union

from http_dispatcher.dispatcher import HttpException
from utils.log_reader import LogFileReader
from utils import run_configs, process_util, et_run_info, common_util
from utils.process_util import ProcessManager
from . import et_util
from .interface import IEasyTierAdapter

logger = logging.getLogger(__name__)

# 延迟初始化：使用线程安全的单例模式
_pm = {}
_pm_lock = threading.Lock()

def _get_process_manager(profile: str = None) -> Union[ProcessManager]:
    """获取 ProcessManager 实例（延迟初始化，线程安全）"""
    if not profile:
        raise HttpException('validate.profile_required')
    pm_key = profile

    # 双重检查锁定模式，保证线程安全的同时提高性能
    cur_pm = _pm.get(pm_key)
    if cur_pm is not None:
        return cur_pm

    with _pm_lock:
        # 再次检查，防止在获取锁期间已被其他线程创建
        cur_pm = _pm.get(pm_key)
        if cur_pm is None:
            pid_file = run_configs.et_pid_file(profile)
            cur_pm = process_util.ProcessManager(pid_file.replace('.toml', ''))
            _pm[pm_key] = cur_pm
    return cur_pm


class CoreForegroundAdapter(IEasyTierAdapter):

    def __init__(self, cli_path: str, core_path: str):
        self._cli_path = cli_path
        self._core_path = core_path

    def get_version(self) -> str:
        cmd = [self._core_path, '--version']
        try:
            raw_version = common_util.run_cmd(cmd)
            return raw_version.replace('easytier-core ', '')
        except Exception:
            logger.exception(f"获取ET版本失败：{cmd}")
            return "unknown"

    def start_network(self, toml_path: str, instance_name: str) -> None:
        rpc_port = et_util.get_available_port(start_port=16888)
        rpc_portal = f"127.0.0.1:{rpc_port}"
        info = et_run_info.get(instance_name)
        # 使用用列表传参，避免执行文件路径含空格，导致报错找不到文件
        cmd = [
            f"{self._core_path}",
            "-c",
            toml_path,
            "-r",
            rpc_portal,
            f"--file-log-dir", f"{run_configs.log_dir()}",
            f"--file-log-level", f"{info.log_level or 'error'}",
            f"--file-log-size", f"50"  # 单个文件日志大小，单位 MB，默认值为 100MB
        ]
        logging.info(f"启动ET命令: {cmd}")
        pm = _get_process_manager(instance_name)
        pm.start(cmd)
        et_run_info.save(instance_name, rpc_portal, info.autostart, False)

    def stop_network(self, instance_name: str) -> None:
        logging.info(f"停止ET配置: {instance_name}")
        pm = _get_process_manager(instance_name)
        pm.stop(timeout=0)

    def status(self, instance_name: str) -> bool:
        pm = _get_process_manager(instance_name)
        return pm.status()

    def get_peers(self, instance_name: str, relay_path: bool = False, proxy_info: bool = True) -> list[dict]:
        if relay_path or proxy_info:
            return self._get_peers_by_route(instance_name, relay_path, proxy_info)
        info = et_run_info.get(instance_name)
        if not info:
            logger.debug(f"未找到配置元数据：{instance_name}")
            return []
        if not info.rpc_portal:
            logger.debug(f"元数据没有rpc信息：{info.__dict__}")
            return []
        cmd = f"{self._cli_path} -o json --rpc-portal {info.rpc_portal} peer"
        try:
            result = common_util.run_cmd(cmd)
            return json.loads(result)
        except Exception as e:
            if str(e).find('failed to connect to server') > 0:
                logger.debug(str(e))
                return []
            raise e

    def check_peers(self, peer_uris: list[str], max_wait_second: int = 6) -> dict:
        core_path = self._core_path
        rpc_port = et_util.get_available_port(16888, 65535)
        random_string = et_util.random_string(16)

        cmd = [
            core_path,
            '--console-log-level', 'ERROR',
            '--no-listener',
            '--private-mode', 'true',
            '--rpc-portal', str(rpc_port),
            '--network-name', random_string,
            '--network-secret', random_string
        ]

        for peer in peer_uris:
            cmd.extend(['-p', peer])

        logger.info(f"启动检测进程，RPC端口: {rpc_port}")

        pm = ProcessManager()
        pm.start(cmd, wait_seconds=0.5, raise_on_failure=False)
        if not pm.status():
            logger.info(f"进程启动失败")
            return {'success': {}, 'fail': list(peer_uris)}

        logger.info(f"检测进程启动成功")
        logger.info(f"等待 RPC 服务就绪 (127.0.0.1:{rpc_port})...")

        rpc_ready = False
        rpc_check_start = time.time()
        rpc_check_timeout = 10
        while (time.time() - rpc_check_start) < rpc_check_timeout:
            if not pm.status():
                logger.info(f"进程已退出")
                return {'success': {}, 'fail': list(peer_uris)}

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result_code = sock.connect_ex(('127.0.0.1', rpc_port))
                sock.close()
                if result_code == 0:
                    rpc_ready = True
                    logger.info(f"RPC 服务已就绪")
                    break
            except Exception:
                pass
            time.sleep(0.5)

        result = None

        try:
            if not rpc_ready:
                raise Exception(f"EasyTier 服务未在 {rpc_check_timeout} 秒内就绪")

            start_check_time = time.time()
            while (time.time() - start_check_time) < max_wait_second:
                if not pm.status():
                    raise Exception(f"EasyTier 服务已退出")

                time.sleep(3)
                result = self._check_peers_available_use_peer(rpc_port, peer_uris)
                logger.debug(f"节点检测结果: {result}")
                if len(result['fail']) == 0:
                    break
                logger.info(f"继续检测未连接节点")

            return result

        finally:
            pm.stop(timeout=0)

    def _check_peers_available_use_peer(self, rpc_port: int, peer_list: list[str]) -> dict:
        cli_path = self._cli_path

        cmd = [
            cli_path,
            '-v',
            '-p', f'127.0.0.1:{rpc_port}',
            '-o', 'json',
            'peer'
        ]

        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'ignore',
        }
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(cmd, **kwargs)

        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            logger.info("检测命令超时")
            process.kill()
            process.wait()
            return {'success': {}, 'fail': []}

        if process.returncode != 0:
            logger.info(f"检测命令执行失败: {stderr}")
            return {'success': {}, 'fail': []}

        data = json.loads(stdout)

        fail_peers = list(peer_list)
        success_peers = {}

        for item in data:
            route = item.get('route', {})
            hostname = route.get('hostname', '').replace('PublicServer_', '')
            result = {
                'relay': route.get('feature_flag', {}).get('avoid_relay_data', True) == False,
                'hostname': hostname,
            }
            conns = item.get('peer', {}).get('conns', [])
            if len(conns) > 0:
                uri = conns[0].get('tunnel', {}).get('remote_addr', {}).get('url')
                result['uri'] = uri
                latency_us = float(conns[0].get('stats', {}).get('latency_us', 0))
                result['latency'] = max(1, latency_us // 1000)
                result['dynamic'] = uri.lower().startswith('txt')
                if uri in fail_peers:
                    fail_peers.remove(uri)
                    success_peers[uri] = result

        return {
            'success': success_peers,
            'fail': fail_peers
        }

    def _fetch_proxy_info(self, instance_name: str) -> dict:
        info = et_run_info.get(instance_name)
        if not info or not info.rpc_portal:
            return {}
        cmd = f"{self._cli_path} -o json --rpc-portal {info.rpc_portal} proxy"
        try:
            result = common_util.run_cmd(cmd)
            data = json.loads(result)
        except Exception as e:
            logger.debug(f"获取proxy信息失败: {e}")
            return {}
        grouped = {}
        if isinstance(data, list):
            items = data
        else:
            return {}
        for item in items:
            if not isinstance(item, dict):
                continue
            dst_raw = item.get('dst') or ''
            dst_ip = dst_raw.split(':')[0] if dst_raw else ''
            transport_type = item.get('transport_type')
            if dst_ip and transport_type:
                grouped.setdefault(dst_ip, set()).add(transport_type)
        return grouped

    @staticmethod
    def _match_proxy_for_node(proxy_map: dict, node_ipv4: str, proxy_cidrs: list) -> list:
        matched_ips = set()

        if node_ipv4 and node_ipv4 in proxy_map:
            matched_ips.add(node_ipv4)

        networks = []
        for cidr in proxy_cidrs or []:
            try:
                networks.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                pass

        if networks:
            for dst_ip in proxy_map.keys():
                try:
                    ip = ipaddress.ip_address(dst_ip)
                    for net in networks:
                        if ip in net:
                            matched_ips.add(dst_ip)
                            break
                except ValueError:
                    pass

        result = []
        for dst_ip in sorted(matched_ips):
            types_set = proxy_map.get(dst_ip, set())
            result.append({
                'proxy_ip': dst_ip,
                'transport_type': sorted(types_set),
            })
        return result

    def _get_peers_by_route(self, instance_name: str, relay_path: bool = False, proxy_info: bool = True) -> list[dict]:
        info = et_run_info.get(instance_name)
        if not info:
            logger.debug(f"未找到配置元数据：{instance_name}")
            return []
        if not info.rpc_portal:
            logger.debug(f"元数据没有rpc信息：{info.__dict__}")
            return []
        cmd = f"{self._cli_path} -v --rpc-portal {info.rpc_portal} route list"
        try:
            result = common_util.run_cmd(cmd)
            route_list_data = json.loads(result)
            items = []

            node_info = route_list_data.get('node_info', {})
            if node_info:
                ipv4_cidr = node_info.get('ipv4_addr', '')
                ipv4 = ipv4_cidr.split('/')[0] if ipv4_cidr else ''
                stun = node_info.get('stun_info')
                items.append({
                    'cidr': ipv4_cidr,
                    'ipv4': ipv4,
                    'hostname': node_info.get('hostname', ''),
                    'cost': 'Local',
                    'lat_ms': '-',
                    'loss_rate': '-',
                    'rx_bytes': '-',
                    'tx_bytes': '-',
                    'tunnel_proto': '-',
                    'nat_type': et_util.format_nat_type(stun.get('udp_nat_type')) if stun else 'Unknown',
                    'id': str(node_info.get('peer_id', '')),
                    'version': node_info.get('version', ''),
                    'proxy_cidrs': node_info.get('proxy_cidrs') or [],
                    'peer_uri': None
                })

            seen = set()
            peer_route_map = {}
            for pr in route_list_data.get('peer_routes', []):
                peer_info = pr.get('peer') or {}
                route = pr.get('route') or {}
                if not route:
                    continue
                pid = peer_info.get('peer_id') or route.get('peer_id')
                if pid is None:
                    continue
                peer_route_map[pid] = (pr, peer_info, route)

            for pid, (pr, peer_info, route) in peer_route_map.items():
                if pid in seen:
                    continue
                seen.add(pid)
                ipv4_inet = route.get('ipv4_addr')
                ipv4_cidr = et_util.inet_to_str(ipv4_inet)
                ipv4 = et_util.addr_to_ipv4(ipv4_inet.get('address') if ipv4_inet else None)
                stun = route.get('stun_info')
                cost = route.get('cost', 0)

                peer_uri = None
                if route.get('feature_flag', {}).get('is_public_server', False):
                    conns = peer_info.get('conns', [])
                    if len(conns) > 0:
                        peer_uri = conns[0].get('tunnel', {}).get('remote_addr', {}).get('url', {})

                if cost == 1:
                    lat_ms = et_util.get_latency_ms(peer_info)
                else:
                    lat_first = route.get('path_latency_latency_first')
                    lat_ms = f'{float(lat_first):.2f}' if lat_first is not None else '-'

                has_peer = bool(pr.get('peer'))

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
                            # 'peer_id': str(cur_route.get('peer_id', '')),
                            'hostname': cur_route.get('hostname', ''),
                            # 'ipv4': et_util.addr_to_ipv4(
                            #     cur_ipv4_inet.get('address') if cur_ipv4_inet else None
                            # ),
                            'remote_addrs': et_util.get_remote_addrs(cur_peer_info),
                            # 'lat_ms': et_util.get_latency_ms(cur_peer_info)
                            # if is_first_hop else None,
                        })
                        if next_hop == cur_pid or next_hop is None:
                            break
                        cur_pid = next_hop
                    relay.reverse()
                    relay = relay[:1]

                items.append({
                    'cidr': ipv4_cidr,
                    'ipv4': ipv4,
                    'hostname': route.get('hostname', ''),
                    'cost': et_util.format_cost(cost),
                    'lat_ms': lat_ms,
                    'loss_rate': et_util.get_loss_rate(peer_info) if has_peer else '0.0%',
                    'rx_bytes': et_util.get_rx_bytes(peer_info) if has_peer else '0 B',
                    'tx_bytes': et_util.get_tx_bytes(peer_info) if has_peer else '0 B',
                    'tunnel_proto': et_util.get_conn_protos(peer_info) if has_peer else '',
                    'nat_type': et_util.format_nat_type(stun.get('udp_nat_type')) if stun else 'Unknown',
                    'id': str(route.get('peer_id', '')),
                    'version': route.get('version', '') or 'unknown',
                    'relay_path': relay,
                    'proxy_cidrs': route.get('proxy_cidrs') or [],
                    'peer_uri': peer_uri,
                })

            items.sort(key=lambda x: (
                0 if x['cost'] == 'Local' else 1,
                x['ipv4'] if x['ipv4'] else '255.255.255.255',
            ))
            if proxy_info:
                proxy_map = self._fetch_proxy_info(instance_name)
                for item in items:
                    node_ipv4 = item.get('ipv4') or ''
                    node_proxy_cidrs = list(item.get('proxy_cidrs') or [])
                    item['proxy_info'] = self._match_proxy_for_node(proxy_map, node_ipv4, node_proxy_cidrs)
                    for p in item['proxy_info']:
                        p_ip = p['proxy_ip']
                        matched = False
                        try:
                            pip = ipaddress.ip_address(p_ip)
                            for c in node_proxy_cidrs:
                                try:
                                    if pip in ipaddress.ip_network(c, strict=False):
                                        matched = True
                                        break
                                except ValueError:
                                    pass
                        except ValueError:
                            pass
                        if not matched:
                            node_proxy_cidrs.insert(0, p_ip)
                    item['proxy_cidrs'] = node_proxy_cidrs
            return items
        except Exception as e:
            if str(e).find('failed to connect to server') > 0:
                logger.debug(str(e))
                return []
            raise e

    def change_log_level(self, log_level: str, **kwargs) -> None:
        log_level = 'disabled' if log_level == 'off' else log_level
        log_level = 'warning' if log_level == 'warn' else log_level
        rpc_portal = kwargs.get('rpc_portal')
        cmd = [
            f"{self._cli_path}",
            "--rpc-portal",
            rpc_portal,
            "logger",
            "set",
            log_level,
        ]
        logger.info(f"设置日志级别命令： {cmd}")
        common_util.run_cmd(cmd)

    def get_logs(self, params: dict) -> dict:
        params = params or {}
        max_lines = min(int(params.get('lines', 20)), 1000)
        offset = int(params.get('offset', 0))

        log_file = Path(run_configs.log_dir()) / f"easytier.log"
        return LogFileReader.read(log_file, offset=offset, max_lines=max_lines, max_bytes=128 * 1024)