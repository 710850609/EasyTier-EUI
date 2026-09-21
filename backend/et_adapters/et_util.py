#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTier 通用工具函数 —— 从 CoreForegroundAdapter / FfiAdapter 提取合并"""

import random
import socket
import string as _string
import sys

# ============================================================
# 常量
# ============================================================

NAT_TYPE_NAMES = {
    0: 'Unknown',
    1: 'OpenInternet',
    2: 'NoPAT',
    3: 'FullCone',
    4: 'Restricted',
    5: 'PortRestricted',
    6: 'Symmetric',
    7: 'SymUdpFirewall',
    8: 'SymmetricEasyInc',
    9: 'SymmetricEasyDec',
}

KNOWN_SCHEMES = {'tcp', 'udp', 'wg', 'quic', 'ws', 'wss', 'faketcp'}


# ============================================================
# 基础工具
# ============================================================

def get_available_port(start_port: int = 15888, end_port: int = 65535) -> int:
    """在指定范围内查找可用端口"""
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.bind(('0.0.0.0', port))
                if sys.platform == 'win32':
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                        s2.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f'在范围 {start_port}-{end_port} 内找不到可用端口')


def random_string(length: int = 16) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(_string.ascii_letters + _string.digits, k=length))


# ============================================================
# 地址 / 网络相关
# ============================================================

def addr_to_ipv4(addr) -> str:
    """将 IPv4 地址（整数 或 {'addr': int} 字典）转为点分十进制字符串"""
    if isinstance(addr, dict):
        addr = addr.get('addr', 0)
    if not addr:
        return ''
    return '.'.join(str((addr >> (i * 8)) & 0xFF) for i in range(3, -1, -1))


def inet_to_str(inet_obj: dict) -> str:
    """将 IPv4 网段对象转为 CIDR 字符串，如 '10.0.0.1/24'"""
    if not inet_obj:
        return ''
    ip = addr_to_ipv4(inet_obj.get('address'))
    length = inet_obj.get('network_length', 32)
    return f'{ip}/{length}' if ip else ''


def uuid_to_str(uuid_obj: dict) -> str:
    """将 UUID 对象转为标准 UUID 字符串"""
    if not uuid_obj:
        return ''
    high = (uuid_obj.get('part1', 0) << 32) | uuid_obj.get('part2', 0)
    low = (uuid_obj.get('part3', 0) << 32) | uuid_obj.get('part4', 0)
    s = f'{high:016x}{low:016x}'
    return f'{s[0:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:32]}'


def is_ipv6_url(url_str: str) -> bool:
    """判断 URL 中的主机部分是否为 IPv6（即 :// 后以 [ 开头）"""
    if not url_str or '://' not in url_str:
        return False
    return url_str.split('://', 1)[1].startswith('[')


def is_ipv6_tunnel(tunnel_type: str, tunnel: dict) -> bool:
    """判断隧道是否为 IPv6"""
    if '://' in tunnel_type:
        _, rest = tunnel_type.split('://', 1)
        if rest.startswith('['):
            return True
    for addr_key in ('resolved_remote_addr', 'local_addr', 'remote_addr'):
        addr = tunnel.get(addr_key, {})
        url = addr.get('url', '') if isinstance(addr, dict) else ''
        if is_ipv6_url(url):
            return True
    return False


def format_tunnel_type(tunnel: dict) -> str:
    """格式化隧道类型字符串，IPv6 隧道追加 '6' 后缀"""
    tunnel_type = tunnel.get('tunnel_type', '')
    if not tunnel_type:
        return ''
    is_v6 = is_ipv6_tunnel(tunnel_type, tunnel)
    if '://' in tunnel_type:
        scheme = tunnel_type.split('://', 1)[0]
    else:
        scheme = tunnel_type
    base = scheme.rstrip('6')
    if base in KNOWN_SCHEMES:
        return f'{base}6' if is_v6 else base
    return scheme


# ============================================================
# 数值格式化
# ============================================================

def humanize_bytes(size, for_short: bool = False) -> str:
    """将字节数转为可读格式

    for_short=False: 1.46 KB, 15.00 MB, 5.20 GB
    for_short=True:  1.46 K, 15 M, 5.20 G（单位单字母，≥10 时省略小数）
    """
    if isinstance(size, str):
        size = int(size)
    unit_names = ['B', 'KB', 'MB', 'GB', 'TB']
    for unit in unit_names:
        if abs(size) < 1024:
            if for_short and size >= 10:
                return f'{int(size)} {unit}'
            return f'{size:.2f} {unit}'
        size /= 1024
    return f'{size:.2f} PB'


def latency_to_ms(latency_us) -> float:
    """微秒延迟转毫秒"""
    if isinstance(latency_us, str):
        latency_us = int(latency_us)
    if not latency_us or latency_us <= 0:
        return 0
    return round(latency_us / 1000, 2)


def format_nat_type(nat_type) -> str:
    """格式化 NAT 类型为可读字符串"""
    if isinstance(nat_type, str):
        try:
            nat_type = int(nat_type)
        except ValueError:
            return nat_type
    return NAT_TYPE_NAMES.get(nat_type, 'Unknown')


def format_cost(cost: int) -> str:
    """格式化路由代价"""
    if cost == 0:
        return 'Local'
    if cost == 1:
        return 'p2p'
    return f'relay({cost})'


# ============================================================
# Peer 信息提取
# ============================================================

def get_latency_ms(peer_info: dict) -> str:
    """从 peer 信息中提取延迟（毫秒），优先取默认连接的延迟"""
    conns = peer_info.get('conns', [])
    default_id_str = uuid_to_str(peer_info.get('default_conn_id'))
    best = None
    for conn in conns:
        stats = conn.get('stats')
        if not stats:
            continue
        if default_id_str and conn.get('conn_id', '') == default_id_str:
            return f'{float(stats.get("latency_us", 0)) / 1000.0:.2f}'
        lat = float(stats.get('latency_us', 0))
        if best is None or lat < best:
            best = lat
    if best is not None:
        return f'{best / 1000.0:.2f}'
    return '-'


def get_loss_rate(peer_info: dict) -> str:
    """从 peer 信息中提取丢包率"""
    default_id_str = uuid_to_str(peer_info.get('default_conn_id'))
    best = None
    for conn in peer_info.get('conns', []):
        lr = conn.get('loss_rate', 0.0)
        if default_id_str and conn.get('conn_id', '') == default_id_str:
            return f'{lr * 100.0:.1f}%'
        if best is None:
            best = lr
    if best is not None:
        return f'{best * 100.0:.1f}%'
    return '-'


def get_rx_bytes(peer_info: dict) -> str:
    """从 peer 信息中提取接收字节数"""
    total = 0
    for conn in peer_info.get('conns', []):
        stats = conn.get('stats')
        if stats:
            total += float(stats.get('rx_bytes', 0))
    return humanize_bytes(total) if total else '-'


def get_tx_bytes(peer_info: dict) -> str:
    """从 peer 信息中提取发送字节数"""
    total = 0
    for conn in peer_info.get('conns', []):
        stats = conn.get('stats')
        if stats:
            total += float(stats.get('tx_bytes', 0))
    return humanize_bytes(total) if total else '-'


def get_conn_protos(peer_info: dict) -> str:
    """从 peer 信息中提取连接协议列表"""
    protos = []
    for conn in peer_info.get('conns', []):
        tunnel = conn.get('tunnel')
        if not tunnel:
            continue
        tt = format_tunnel_type(tunnel)
        if tt and tt not in protos:
            protos.append(tt)
    return ','.join(protos) if protos else '-'


def get_remote_addrs(peer_info: dict) -> list[str]:
    """从 peer 信息中提取远端地址列表"""
    addrs = []
    for conn in peer_info.get('conns', []):
        tunnel = conn.get('tunnel')
        if not tunnel:
            continue
        url = (
            tunnel.get('resolved_remote_addr', {}).get('url', '')
            or tunnel.get('remote_addr', {}).get('url', '')
        )
        if url and url not in addrs:
            addrs.append(url)
    return addrs