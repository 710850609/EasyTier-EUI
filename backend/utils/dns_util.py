#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dns.resolver
import os
import subprocess

_resolver = None


def _get_resolver():
    global _resolver
    if _resolver is not None:
        return _resolver
    if os.path.isfile('/etc/resolv.conf'):
        _resolver = dns.resolver.get_default_resolver()
    else:
        # 创建适用于 Android 的 DNS Resolver
        _resolver = dns.resolver.Resolver(configure=False)
        nameservers = []
        try:
            for key in ['net.dns1', 'net.dns2', 'net.dns3', 'net.dns4']:
                result = subprocess.run(['getprop', key], capture_output=True, text=True, timeout=2)
                ns = result.stdout.strip()
                if ns:
                    nameservers.append(ns)
        except Exception:
            pass
        if not nameservers:
            nameservers = ['114.114.114.114', '223.5.5.5', '119.29.29.29']
        _resolver.nameservers = nameservers
    return _resolver


def get_dns_txt_records(domain, timeout=5):
    """获取域名的所有 TXT 记录"""
    try:
        answers = _get_resolver().resolve(domain, 'TXT', lifetime=timeout)
        records = []
        for rdata in answers:
            # TXT 记录可能包含多个字符串段，拼接起来
            txt = ''.join([s.decode('utf-8') for s in rdata.strings])
            records.append(txt)
        return records
    except dns.resolver.NXDOMAIN:
        return []  # 域名不存在
    except dns.resolver.NoAnswer:
        return []  # 无 TXT 记录
    except dns.resolver.LifetimeTimeout:
        return []  # DNS 查询超时
    except Exception as e:
        raise

# 示例
if __name__ == "__main__":
    domain = "google.com"
    domain = "github-proxy.v6.army"
    txt_records = get_dns_txt_records(domain)
    for record in txt_records:
        print(f"TXT: {record}")