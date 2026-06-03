# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import socket
import ipaddress
import psutil
import platform
from typing import List, Dict, Optional, Tuple

_VIRTUAL_KEYWORDS = (
    "vmware", "virtualbox", "hyper-v", "virtual",
    "docker", "tap", "tun", "vpn", "pseudo", "miniport",
    "wsl", "loopback", "lo", "teredo", "isatap", "6to4",
    "nordlynx", "wireguard", "zerotier", "hamachi",
    "cisco", "anyconnect", "sangfor", "fortinet",
    "checkpoint", "paloalto", "atrust", "ppp", "ras", "ndis",
    "br-", "virbr", "vmnet", "dummy", "ifb", "sit", "gre",
    "ipip", "ip6tnl", "vti", "bridge", "hyp",
    "utun", "awdl", "llw", "gif", "stf",
)


def _get_default_gateways() -> set:
    """
    获取所有默认网关对应的网卡名。
    返回网卡名集合（小写），用于匹配。
    """
    gateways = set()
    try:
        gws = psutil.net_if_addrs()
        # psutil.net_if_stats() 的 key 是网卡名
        # 但默认网关信息在 psutil.net_if_addrs() 里没有
        # 需要用 psutil.net_if_addrs() + 路由表推断，或者直接用 net_connections
        # 更直接的方式：通过默认网关的 IP 反查网卡

        # 获取系统默认网关信息
        default_gw = psutil.net_if_addrs()

        # 跨平台获取默认网关：通过 socket + 路由表
        # Windows: 用 GetIpForwardTable / GetBestRoute
        # Linux/macOS: 读取 /proc/net/route 或执行 ip route

        # 更通用的方式：通过连接外部IP，看用哪个本地IP出去
        # 但这需要网络访问，不够稳定

        # 最稳的方式：直接解析系统路由表
        gateways = _parse_default_gateway()
    except Exception:
        pass
    return gateways


def _parse_default_gateway() -> set:
    """
    跨平台解析默认网关，返回网卡名集合（小写）。
    """
    system = platform.system()
    gateways = set()

    if system == "Windows":
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Select-Object -ExpandProperty InterfaceAlias"],
                capture_output=True, text=True, timeout=5, creationflags = subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if line:
                    gateways.add(line.lower())
        except Exception:
            pass

    elif system == "Linux":
        try:
            with open("/proc/net/route") as f:
                for line in f.readlines()[1:]:  # 跳过表头
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[1] == "00000000":  # destination 0.0.0.0
                        iface = parts[0]
                        gateways.add(iface.lower())
        except Exception:
            pass

    elif system == "Darwin":  # macOS
        try:
            import subprocess
            result = subprocess.run(
                ["netstat", "-rn"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 6 and parts[0] == "default":
                    iface = parts[-1]  # 最后一列是网卡名
                    gateways.add(iface.lower())
        except Exception:
            pass

    return gateways


def _is_virtual_nic(name: str, has_valid_ip: bool) -> bool:
    name_lower = name.lower()

    if name_lower.startswith("vethernet"):
        return not has_valid_ip

    if platform.system() == "Linux" and name_lower.startswith("veth"):
        return True

    for kw in _VIRTUAL_KEYWORDS:
        if kw in name_lower:
            return True

    return False


def get_lan_ips(
        exclude_virtual: bool = True,
        only_private: bool = True,
        exclude_down: bool = True,
        only_default_gateway: bool = True,  # 新增：只保留有默认网关的网卡
) -> List[Dict[str, str]]:
    """
    获取本地IP
    返回key name, ip, netmask
    """
    results: List[Dict[str, str]] = []
    stats = psutil.net_if_stats() if exclude_down else {}
    addrs = psutil.net_if_addrs()

    # 获取默认网关对应的网卡名
    default_gw_ifaces = _parse_default_gateway() if only_default_gateway else set()

    for name, addr_list in addrs.items():
        # 过滤未启用的网卡
        if exclude_down and name in stats and not stats[name].isup:
            continue

        # 只保留有默认网关的网卡
        if only_default_gateway and name.lower() not in default_gw_ifaces:
            continue

        for addr in addr_list:
            if addr.family != socket.AF_INET:
                continue

            ip_str = addr.address

            if ip_str.startswith("127.") or ip_str.startswith("169.254.") or ip_str == "0.0.0.0":
                continue

            is_private = False
            try:
                is_private = ipaddress.ip_address(ip_str).is_private
            except ValueError:
                continue

            if only_private and not is_private:
                continue

            if exclude_virtual:
                has_valid = is_private and not ip_str.startswith("169.254.")
                if _is_virtual_nic(name, has_valid):
                    continue

            results.append({
                "name": name,
                "ip": ip_str,
                "netmask": addr.netmask or "",
            })

    return results


if __name__ == "__main__":
    ips = get_lan_ips()
    print("本机局域网 IP（仅默认网关网卡）：")
    for info in ips:
        print(f"  {info['name']:35s} -> {info['ip']}/{info['netmask']}")


    ips = get_lan_ips()
    ip_list = []
    for item in ips:
        ip = item['ip']
        arr = ip.split('.')
        ip_list.append(f"{arr[0]}.{arr[1]}.{arr[2]}.1/32")
        ip_list.append(f"{arr[0]}.{arr[1]}.1.1/24")
        print(ip_list)
