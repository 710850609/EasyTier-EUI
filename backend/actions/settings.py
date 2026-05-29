#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from http_dispatcher.dispatcher import HttpException
from utils import run_configs


def build_version(*kwargs):
    return run_configs.build_version()

def save_github_mirror(data, *kwargs):
    url = data['url'] or ''
    try:
        github_proxy_file = run_configs.github_proxy_file()
        cfg_path = Path(github_proxy_file)
        cfg_path.write_text(url.strip())
        return '保存成功'
    except Exception as e:
        logging.error(f"保存代理配置失败: {e}")
        raise HttpException(f"保存代理配置失败: {e}") from e

def github_mirrors(*kwargs):
    try:
        github_proxy_file = run_configs.github_proxy_file()
        selected = ''
        cfg_path = Path(github_proxy_file)
        if cfg_path.exists():
            content = cfg_path.read_text().strip()
            # 去除空行
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            selected = lines[0] if lines else ""
        #  https://github.akams.cn/
        sources = [
            { "value": "https://gh-proxy.org", "label": "gh-proxy.org", "support_pi": True},
            { "value": "https://gh.felicity.ac.cn", "label": "gh.felicity.ac.cn", "support_pi": True},
            { "value": "https://ghfast.top", "label": "ghfast.top", "support_pi": False},
            { "value": "https://ghproxy.net", "label": "ghproxy.net", "support_pi": False},
            { "value": "https://gh.llkk.cc", "label": "gh.llkk.cc", "support_pi": False},
            { "value": "https://github-proxy.memory-echoes.cn", "label": "github-proxy.memory-echoes.cn", "support_pi": False},
            { "value": "https://gh.b52m.cn", "label": "gh.b52m.cn", "support_pi": False},
        ]

        # ── 新增：并发测速 ──
        def _test_speed(item):
            proxy = item["value"]
            # 使用 GitHub 轻量文件测试，HEAD 请求减少流量
            test_path = "https://raw.githubusercontent.com/github/gitignore/main/README.md"
            test_url = f"{proxy}/{test_path}" if proxy else test_path

            start = time.time()
            try:
                resp = requests.head(test_url, timeout=4, allow_redirects=True)
                if resp.status_code < 400:
                    elapsed = (time.time() - start) * 1
                    item["delay"] = round(elapsed, 2)
                    item["status"] = "ok"
                    item["desc"] = ""
                else:
                    item["delay"] = -1
                    item["status"] = f"http_{resp.status_code}"
                    item["desc"] = f"不可用(HTTP {resp.status_code})"
            except requests.exceptions.Timeout:
                item["delay"] = -1
                item["status"] = "timeout"
                item["desc"] = f"超时"
            except Exception:
                item["delay"] = -1
                item["status"] = str(e)
                item["desc"] = f"不可用"
            return item

        # 并发测速（线程数 = 代理数量）
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            list(executor.map(_test_speed, sources))

        # 按速度排序：可用（speed > 0）的在前，按延迟升序；不可用的（-1）放最后
        sources.sort(key=lambda x: (x.get("delay", -1) == -1, x.get("delay", -1)))
        sources.insert(0, { "value": "", "label": "不使用"})
        return { 'selected': selected, 'sources': sources }
    except Exception as e:
        logging.warning(f"读取代理配置失败: {e}")
        raise HttpException(f"读取代理配置失败: {e}") from e
