#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android 平台进程工具 - 替代 psutil
"""

import os
import re
import time
from typing import Optional, Dict


def get_process_info(pid: int) -> Optional[Dict]:
    try:
        stat_path = f"/proc/{pid}/stat"
        status_path = f"/proc/{pid}/status"
        if not os.path.exists(stat_path):
            return None
        with open(stat_path, 'r') as f:
            stat = f.read().strip()
        match = re.match(
            r'(\d+)\s+\((.+)\)\s+(\w)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)',
            stat
        )
        if not match:
            return None
        comm = match.group(2)
        state = match.group(3)
        utime = int(match.group(14))
        stime = int(match.group(15))
        mem_rss = 0
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        mem_rss = int(line.split()[1])
                        break
        cpu_time = (utime + stime) / os.sysconf(os.sysconf_names['SC_CLK_TCK'])
        return {
            'pid': pid, 'name': comm, 'status': state,
            'cpu_percent': 0.0, 'memory_rss': mem_rss, 'cpu_time': cpu_time,
        }
    except Exception:
        return None


def get_cpu_usage(pid: int, interval: float = 0.5) -> float:
    info1 = get_process_info(pid)
    if not info1:
        return 0.0
    time.sleep(interval)
    info2 = get_process_info(pid)
    if not info2:
        return 0.0
    cpu_diff = info2['cpu_time'] - info1['cpu_time']
    return max(0.0, min((cpu_diff / interval) * 100.0, 100.0))


def get_memory_usage(pid: int) -> int:
    info = get_process_info(pid)
    return info.get('memory_rss', 0) if info else 0


def is_process_running(pid: int) -> bool:
    return os.path.exists(f"/proc/{pid}")


def get_system_cpu_count() -> int:
    return os.cpu_count() or 4


def get_system_memory_total() -> int:
    try:
        with open("/proc/meminfo", 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1])
    except Exception:
        pass
    return 0


def get_system_memory_available() -> int:
    try:
        with open("/proc/meminfo", 'r') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    return int(line.split()[1])
    except Exception:
        pass
    return 0