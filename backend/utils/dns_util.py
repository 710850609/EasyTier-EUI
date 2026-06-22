#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dns.resolver

def get_dns_txt_records(domain, timeout=5):
    """获取域名的所有 TXT 记录"""
    try:
        answers = dns.resolver.resolve(domain, 'TXT', lifetime=timeout)
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