#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import json
import logging
import re
import threading
import time
# 在进程退出时被首次导入，concurrent.futures 的懒加载机制触发了 threading._register_atexit，但此时 interpreter 已进入 shutdown 状态，报错
try:
    from concurrent.futures import ThreadPoolExecutor, as_completed
except RuntimeError:
    pass
from pathlib import Path
from typing import Optional, List, Tuple

import requests

from http_dispatcher.dispatcher import HttpException
from utils import run_configs
from utils.dns_util import get_dns_txt_records


def get_latest_version(api_url) -> str:
    """
    获取最新版本，如：https://api.github.com/repos/EasyTier/easytier-manager/releases/latest
    合适 提取版本号 v1.2.3 -> 1.2.3
    """
    try:
        # response = requests.get(api_url, timeout=30)
        # response.raise_for_status()
        # data = response.json()
        data = get_api(api_url)

        tag_name = data.get('tag_name', '')
        # 提取版本号 v1.2.3 -> 1.2.3
        match = re.search(r'(\d+\.\d+\.\d+)', tag_name)
        if match:
            return match.group(1)
        raise ValueError(f"无法解析版本号: {tag_name}")
    except Exception as e:
        logging.error(f"获取 manager 版本失败: {e}")
        raise

# def get_github_proxy() -> str:
#     """获取 GitHub 代理 URL"""
#     try:
#         github_proxy_file = run_configs.github_proxy_file()
#         if not Path(github_proxy_file).exists():
#             logging.warning(f"GitHub加速配置文件不存在: {github_proxy_file}，不使用加速")
#             return None
#         cfg_path = Path(github_proxy_file)
#         if cfg_path.exists():
#             content = cfg_path.read_text().strip()
#             # 去除空行
#             lines = [l.strip() for l in content.split('\n') if l.strip()]
#             return lines[0] if lines else ""
#     except Exception as e:
#         logging.warning(f"读取代理配置失败: {e}")
#     return ""

def get_download_url_proxy(url: str) -> str:
    """获取 GitHub 代理 URL"""
    proxy_urls = get_proxy_urls()
    if proxy_urls and len(proxy_urls) > 0:
        proxy_url = proxy_urls[0]["url"]
        if proxy_url and proxy_url != '':
            logging.info(f"使用加速地址: {proxy_url}")
            url = proxy_url + '/' + url
    return url


def download_raw_file(download_url:str, timeout:int = 10, proxy_url_list:Optional[list] = None):
    proxy_url = ''
    if proxy_url_list and len(proxy_url_list) > 0:
        proxy_url = proxy_url_list[0]
        proxy_url_list.remove(proxy_url)
    request_url = download_url
    if proxy_url and proxy_url != '':
        request_url = f"{proxy_url}/{download_url}"
    response = None
    try:
        response = requests.get(request_url, timeout=timeout)
        response.raise_for_status()
        if 'application/json' not in response.headers['content-type']:
            return response.json()
        else:
            return response.content
    except requests.exceptions.RequestException as e:
        logging.warning(f"获取github文件HTTP异常: {str(e)}")
        if response and response.status_code == 404:
            logging.warning(f"文件不存在: {request_url}")
            raise e
        if proxy_url_list is None:
            proxy_urls = get_proxy_urls()
            if len(proxy_urls) > 0:
                proxy_url_list = [item["url"] for item in proxy_urls]
        if proxy_url_list and len(proxy_url_list) > 0:
            return download_raw_file(download_url, timeout, proxy_url_list)
        raise e
    pass

def get_api(url: str, proxy_url: str = ""):
    """获取 GitHub API 数据"""
    try:
        req_url = copy.copy(url)
        if proxy_url and proxy_url != '':
            req_url = proxy_url + '/' + req_url
        response = requests.get(req_url, timeout=10)
        if response.status_code == 404:
            raise HttpException(f"请求资源不存在: {req_url}")
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"获取 API 数据失败: {e}")
        if not proxy_url or proxy_url == '':
            proxy_urls = get_proxy_urls()
            api_proxy_urls = [item['url'] for item in proxy_urls if item['supports_api']]
            if not api_proxy_urls:
                logging.error("无可用 API 加速地址，无法获取 GitHub API 数据")
                raise e
            for api_proxy_url in api_proxy_urls:
                logging.info(f"尝试使用 API 加速地址: {api_proxy_url}")
                try:
                    return get_api(url, api_proxy_url)
                except requests.exceptions.RequestException as e2:
                    logging.error(f"获取 API 数据失败: {e2}")
            raise e
        else:
            raise e

def get_proxy_urls(refresh:bool = False) -> list:
    """获取 GitHub 代理列表"""
    proxy_file_path = Path(run_configs.data_dir(), 'github_proxy.json')
    cur_time = int(time.time() * 1000)
    if not refresh and proxy_file_path.exists():
        with open(proxy_file_path, 'r', encoding="utf-8") as f:
            cache_data = json.load(f)
            if cache_data and len(cache_data.get('sources', [])) > 0 and cur_time - cache_data.get('create_time', 0) < 1000 * 60 * 60:
                logging.info(f"使用缓存代理列表: {cache_data.get('sources', [])}")
                return cache_data.get('sources', [])

    #  https://github.akams.cn/
    url_list = get_dns_txt_records('github-proxy.v6.army')
    if not url_list:
        logging.warning("DNS TXT 查询返回空，使用默认加速地址")
        url_list = [
            "https://ghfast.top",
            "https://gh-proxy.com",
            "https://gh.llkk.cc",
        ]
    # default_proxy_urls = [
    #     "https://gh.felicity.ac.cn",
    #     "https://gh-proxy.org",
    #     "https://github.dpik.top",
    #     "https://gh.dpik.top",
    # ]
    # src_url = 'https://raw.githubusercontent.com/710850609/EasyTier-EUI/refs/heads/main/configs/github-proxy-urls.json'
    # url_list = download_raw_file(src_url, proxy_url_list=default_proxy_urls)
    # if not url_list or len(url_list) == 0:
    #     logging.info(f"获取github文件失败: {src_url}, 使用默认URL")
    #     url_list = default_proxy_urls
    # logging.info(f"获取到远程代理URL: {url_list}")
    logging.info(f"获取到GitHub 加速地址: {url_list}")
    url_list = [{'url': item} for item in url_list]
    url_list = check_proxy_url(url_list)
    url_list = [item for item in url_list if item['status'] == 'ok']
    logging.debug(f"GitHub加速地址检测结果: {url_list}")
    if url_list and len(url_list) > 0:
        with open(proxy_file_path, 'w', encoding="utf-8") as f:
            f.write(json.dumps({'sources': url_list, 'create_time': cur_time}, indent=2))
    return url_list

def check_proxy_url(url_list:list, check_timeout:int = 3) -> list:
    """
    检查代理 URL 是否有效
    check_type: raw 或 api
    """

    # ── 新增：并发测速 ──
    def _test_speed(item):
        proxy = item["url"]
        result = {"url": proxy, "delay": -1, "status": "", "desc": "", "supports_range": False, "supports_api": False}
        # 使用 GitHub 轻量文件测试，HEAD 请求减少流量
        # test_file_path = "https://raw.githubusercontent.com/github/gitignore/main/README.md"
        # test_file_path = "https://github.com/EasyTier/EasyTier/archive/refs/tags/v2.6.4.zip"
        test_file_path = "https://github.com/710850609/EasyTier-EUI/releases/download/0.9.020604/EasyTier-EUI-fnos-x86_64-0.9.020604.fpk"
        test_api_path = "https://api.github.com/repos/710850609/EasyTier-EUI/releases/latest"
        test_file_url = f"{proxy}/{test_file_path}" if proxy else test_file_path
        test_api_url = f"{proxy}/{test_api_path}" if proxy else test_api_path

        start = time.time()
        try:
            test_headers = {"Range": "bytes=0-0"}
            resp = requests.head(test_file_url, timeout=check_timeout, allow_redirects=True, headers=test_headers)
            if resp.status_code < 400:
                elapsed = (time.time() - start) * 1
                result["delay"] = round(elapsed, 2)
                result["status"] = "ok"
                result["supports_range"] = (resp.status_code == 206)
                try:
                    resp = requests.head(test_api_url, timeout=check_timeout, allow_redirects=True)
                    result["supports_api"] = (resp.status_code == 200)
                except requests.exceptions.RequestException as e:
                    result["supports_api"] = False
            else:
                result["status"] = f"http_{resp.status_code}"
                result["desc"] = f"不可用(HTTP {resp.status_code})"
        except requests.exceptions.Timeout:
            result["status"] = "timeout"
            result["desc"] = f"超时"
        except Exception as e:
            result["status"] = str(e)
            result["desc"] = f"不可用"
        return result

    # 并发测速（线程数 = 代理数量）
    with ThreadPoolExecutor(max_workers=len(url_list)) as executor:
        url_list = list(executor.map(_test_speed, url_list))

    # 按速度排序：可用（speed > 0）的在前，按延迟升序；不可用的（-1）放最后
    url_list.sort(key=lambda x: (x.get("delay", -1) == -1, x.get("delay", -1)))
    return url_list


def download_release_file_bak(url: str, output_path: str, desc: str = ""):
    """下载文件，带进度显示"""
    try:
        url = get_download_url_proxy(url)
        logging.info(f"开始下载: {url}")
        logging.info(f"保存到: {output_path}")
        # 确保 output_path 是 Path 对象（避免重复转换）
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用流式下载
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        # 验证响应内容类型
        content_type = response.headers.get('content-type', '').lower()
        content_length = response.headers.get('content-length', '0')

        logging.info(f"Content-Type: {content_type}")
        logging.info(f"Content-Length: {content_length}")

        # 检查是否是ZIP文件或HTML页面
        if 'text/html' in content_type or int(content_length) < 1000:
            logging.error(f"下载的不是ZIP文件，Content-Type: {content_type}")
            raise Exception(f"下载失败：代理返回的不是有效的文件")

        total_size = int(content_length)
        downloaded = 0

        with open(output_path, 'wb') as f:
            last_percent = -1  # 初始化在循环外
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        current_percent = int(percent)  # 取整
                        # 每增加 1% 打印一次，且只打印一次
                        if current_percent > last_percent:
                            logging.debug(f"{desc} 下载进度: {current_percent}%")
                            last_percent = current_percent

        logging.info(f"下载成功: {output_path}")
    except Exception as e:
        logging.exception(f"下载失败")
        if output_path.exists():
            output_path.unlink()
        raise Exception(f"下载失败：{e}") from e


def _probe_url(url: str, timeout: int = 30) -> Tuple[bool, int, str]:
    """
    探测 URL 是否可用，以及是否支持 Range 下载。
    返回: (支持Range, 文件大小, 实际使用的URL)
    """
    try:
        # 先尝试 HEAD
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        if resp.status_code != 200:
            return False, 0, url

        # 测试 Range 支持
        test_headers = {"Range": "bytes=0-0"}
        resp_range = requests.head(url, headers=test_headers, allow_redirects=True, timeout=timeout)

        supports_range = (resp_range.status_code == 206)
        total_size = int(resp.headers.get("content-length", 0))

        return supports_range, total_size, url
    except Exception as e:
        logging.warning(f"探测 URL 失败: {url} | {e}")
        return False, 0, url


def _download_chunk(
        url: str,
        start: int,
        end: int,
        part_path: Path,
        timeout: int = 300,
        max_retries: int = 3
) -> bool:
    """
    下载文件的 [start, end] 字节段（两端闭合）。
    失败会自动重试，返回是否成功。
    """
    headers = {"Range": f"bytes={start}-{end}"}

    for attempt in range(max_retries):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=timeout) as resp:
                if resp.status_code not in (200, 206):
                    raise Exception(f"HTTP {resp.status_code}")

                with open(part_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                return True
        except Exception as e:
            logging.warning(f"分片下载失败 [{start}-{end}] 第{attempt + 1}次: {e}")
            if part_path.exists():
                part_path.unlink(missing_ok=True)

    return False


def download_release_file(
        download_url: str,
        output_path: str,
        desc: str = "",
        num_threads: int = 4,
        timeout: int = 300,
        progress_callback=None
) -> None:
    """
    多镜像 + 分段并行下载。

    :param download_url: GitHub 下载地址
    :param output_path: 保存路径
    :param desc: 进度描述
    :param num_threads: 分段并行数，默认 4
    :param progress_callback: 进度回调 callback(percent: int, description: str)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    check_result = get_proxy_urls()
    if len(check_result) == 0:
        logging.info(f"无可用加速地址，开始重新获取镜像地址...")
        check_result = get_proxy_urls(refresh=True)

    # ========== 1. 探测可用 URL 和文件大小 ==========
    usable_urls = [ item.get('url')  + '/' + download_url for item in check_result if item.get('delay') >= 0]
    usable_range_urls = [ item.get('url')  + '/' + download_url for item in check_result if item.get('delay') >= 0 and item.get('supports_range', False)]
    if not usable_urls:
        raise Exception("所有镜像地址均不可用")

    # 优先用支持 Range 的地址进行分段下载
    if not usable_range_urls:
        # 全都不支持 Range，回退到单线程，挑第一个可用的
        logging.warning("没有地址支持 Range，回退到单线程下载")
        _download_single(usable_urls[0], output_path, desc, timeout, progress_callback)
        return
    logging.info(f"加速地址可用 {len(usable_urls)} 个，支持 Range 下载 {len(usable_range_urls)} 个")
    resp = requests.head(usable_range_urls[0], allow_redirects=True, timeout=timeout)
    total_size = int(resp.headers.get("content-length", 0))

    # ========== 2. 计算分片 ==========
    # 每段至少 1MB，避免线程过多
    min_chunk = 1024 * 1024
    chunk_size = max(total_size // num_threads, min_chunk)

    chunks: List[Tuple[int, int, Path]] = []
    for i in range(0, total_size, chunk_size):
        start = i
        end = min(i + chunk_size - 1, total_size - 1)  # Range 是闭合区间
        part_path = output_path.parent / f"{output_path.name}.part_{start}_{end}"
        chunks.append((start, end, part_path))

    logging.info(f"{desc} 分片信息: {len(chunks)} 段, 总大小: {total_size}")

    # ========== 3. 并行下载（带故障转移） ==========
    progress_lock = threading.Lock()
    downloaded_total = [0]  # 用 list 做可变引用
    last_percent = [-1]

    def _download_with_fallback(start: int, end: int, part_path: Path) -> bool:
        """尝试所有可用 URL 下载该分片"""
        # 优先用 Range 支持的 URL，失败再试其他
        candidates = usable_range_urls + [u for u in usable_urls if u not in usable_range_urls]

        for url in candidates:
            logging.debug(f"尝试下载 [{start}-{end}] from {url}")
            if _download_chunk(url, start, end, part_path, timeout=timeout):
                with progress_lock:
                    downloaded_total[0] += (end - start + 1)
                    if total_size > 0:
                        p = int(downloaded_total[0] / total_size * 100)
                        if p > last_percent[0]:
                            logging.info(f"{desc} 下载进度: {p}%")
                            last_percent[0] = p
                            if progress_callback:
                                progress_callback(p, desc)
                return True
            logging.warning(f"URL 失败，切换镜像: {url}")

        return False

    failed = False
    try:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_map = {
                executor.submit(_download_with_fallback, s, e, p): (s, e, p)
                for s, e, p in chunks
            }

            for future in as_completed(future_map):
                success = future.result()
                if not success:
                    failed = True
                    # 取消剩余任务（尽力而为）
                    for f in future_map:
                        f.cancel()
                    break

        if failed:
            raise Exception("部分分片下载失败，所有镜像均已尝试")

        # ========== 4. 合并文件 ==========
        logging.info(f"{desc} 下载完成，开始合并...")
        with open(output_path, "wb") as outfile:
            for start, end, part_path in chunks:
                with open(part_path, "rb") as infile:
                    outfile.write(infile.read())
                part_path.unlink(missing_ok=True)

        logging.info(f"{desc} 合并完成: {output_path}")

    except Exception:
        # 清理残片
        for _, _, part_path in chunks:
            part_path.unlink(missing_ok=True)
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        raise


def _download_single(url: str, output_path: Path, desc: str, timeout: int, progress_callback=None):
    """不支持 Range 时的单线程回退"""
    logging.info(f"{desc} 单线程下载: {url}")
    with requests.get(url, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        last_percent = -1
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        p = int(downloaded / total * 100)
                        if p > last_percent:
                            last_percent = p
                            if progress_callback:
                                progress_callback(p, desc)
    logging.info(f"{desc} 下载完成")