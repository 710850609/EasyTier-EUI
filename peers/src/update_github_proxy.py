#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
import urllib
import urllib.request
import urllib.error
from pathlib import Path

# dynv6 API 配置
API_BASE = "https://dynv6.com/api/v2"
# 从环境变量获取 Token，如果没有则使用默认值（需要替换）
DYNV6_TOKEN = os.environ.get("DYNV6_TOKEN")
if not DYNV6_TOKEN and Path("DYNV6_TOKEN.txt").exists():
    print("环境变量未设置，尝试从 DYNV6_TOKEN.txt 读取 Token")
    DYNV6_TOKEN = Path("DYNV6_TOKEN.txt").read_text().strip()
if not DYNV6_TOKEN:
    print("错误: 请设置 DYNV6_TOKEN 环境变量或 DYNV6_TOKEN.txt 文件")
    sys.exit(1)

domain = "github-proxy.v6.army"

# 默认外部 TXT 文件路径
DEFAULT_PROXY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'github-proxy-urls.txt'
)


def update(proxy_file=None):
    """
    从外部 TXT 文件读取 GitHub 代理地址，每行作为一条 TXT 记录写入到同一域名下
    以文件数据为准：文件有的、DNS 没有的→新增；文件没有的、DNS 有的→删除

    Args:
        proxy_file: 外部 TXT 文件路径，每行一个代理 URL
    """
    if proxy_file is None:
        proxy_file = DEFAULT_PROXY_FILE

    proxy_path = Path(proxy_file)
    if not proxy_path.exists():
        print(f"错误: 代理文件不存在: {proxy_path}")
        sys.exit(1)

    # 读取文件，跳过空行和注释行
    lines = []
    with open(proxy_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)

    if not lines:
        print("错误: 代理文件为空")
        sys.exit(1)

    print(f"读取到 {len(lines)} 个代理地址")
    for i, url in enumerate(lines):
        print(f"  {i}. {url}")

    # 获取 zones
    zones = get_zones()
    if not zones:
        print("错误: 获取 zones 失败，退出")
        sys.exit(1)

    # 解析域名，找到 zone 和 record_name
    parts = domain.split('.')
    zone_id = None
    record_name = None

    for i in range(0, len(parts)):
        possible_zone = '.'.join(parts[i:])
        for zone in zones:
            if zone.get('name') == possible_zone:
                zone_id = zone.get('id')
                record_name = '.'.join(parts[:i])
                break
        if zone_id:
            print(f"找到 zone: '{possible_zone}' (id={zone_id})")
            break

    if not zone_id:
        print(f"错误: 未找到域名 {domain} 对应的 zone")
        sys.exit(1)

    print(f"记录名称: '{record_name}'")

    # 获取该 zone 下所有记录，找出同名 TXT 记录
    all_records = get_records(zone_id)
    existing_records = []
    for record in all_records:
        if record.get('type') == 'TXT' and record.get('name') == record_name:
            existing_records.append(record)

    # value -> record 映射
    existing_map = {r.get('data', ''): r for r in existing_records}
    file_values = set(lines)

    success_count = 0
    fail_count = 0

    # 新增：文件中存在但 DNS 中不存在
    for url in lines:
        if url in existing_map:
            continue
        print(f"添加 TXT {domain} -> {url}")
        status, response = api_request(
            "POST",
            f"/zones/{zone_id}/records",
            {"name": record_name, "type": "TXT", "data": url}
        )
        if status in [200, 201]:
            print(f"    ✓ 已添加")
            success_count += 1
        else:
            print(f"    ✗ 失败: {status} - {response}")
            fail_count += 1

    # 删除：DNS 中存在但文件中不存在
    for existing_value, record in existing_map.items():
        if existing_value in file_values:
            continue
        record_id = record.get('id')
        print(f"删除 TXT {domain} -> {existing_value}")
        status, response = api_request(
            "DELETE",
            f"/zones/{zone_id}/records/{record_id}"
        )
        if status in [200, 204]:
            print(f"    ✓ 已删除")
        else:
            print(f"    ✗ 删除失败: {status} - {response}")

    print(f"\n完成: 新增 {success_count}, 失败 {fail_count}")
    return fail_count == 0


def api_request(method, endpoint, data=None):
    """发送 API 请求"""
    url = f"{API_BASE}{endpoint}"

    headers = {
        "Authorization": f"Bearer {DYNV6_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        if data:
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = None

        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=headers,
            method=method
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return -1, str(e)


def get_zones():
    """获取所有 zones"""
    status, response = api_request("GET", "/zones")
    if status == 200:
        return json.loads(response)
    else:
        print(f"获取 zones 失败: {status} - {response}")
        return []


def get_records(zone_id):
    """获取 zone 下的所有记录"""
    status, response = api_request("GET", f"/zones/{zone_id}/records")
    if status == 200:
        return json.loads(response)
    else:
        print(f"获取 records 失败: {status} - {response}")
        return []


if __name__ == '__main__':
    proxy_file = sys.argv[1] if len(sys.argv) > 1 else None
    update(proxy_file)