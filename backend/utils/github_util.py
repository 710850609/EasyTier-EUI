#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import re
import shutil
import threading
import time
import uuid
# 在进程退出时被首次导入，concurrent.futures 的懒加载机制触发了 threading._register_atexit，但此时 interpreter 已进入 shutdown 状态，报错
try:
    from concurrent.futures import ThreadPoolExecutor, as_completed
except RuntimeError:
    pass
from pathlib import Path
from typing import Optional, List, Tuple, Callable

import requests

from http_dispatcher.dispatcher import HttpException
from locales import get_message, get_lang, set_lang
from utils import run_configs
from utils.dns_util import get_dns_txt_records


logger = logging.getLogger(__name__)

# ── 配置常量 ──
PROXY_CACHE_TTL_MS = 1000 * 60 * 60         # 代理列表缓存有效期：1 小时
SMALL_FILE_THRESHOLD = 5 * 1024 * 1024       # 5MB 以下文件跳过并行分片下载
MIN_CHUNK_SIZE = 1024 * 1024                 # 最小分片大小：1MB
PROXY_CHECK_TIMEOUT = 3                       # 代理测速超时（秒）
MAX_PROXY_CHECK_WORKERS = 8                   # 代理测速最大并发线程数
DNS_TXT_DOMAIN = 'github-proxy.v6.army'       # DNS TXT 记录域名
DNS_TIMEOUT = 10                              # DNS 查询超时（秒）
DEFAULT_TEST_FILE_URL = 'https://github.com/710850609/EasyTier-EUI/releases/download/0.9.020604/EasyTier-EUI-fnos-x86_64-0.9.020604.fpk'
DEFAULT_TEST_API_URL = 'https://api.github.com/repos/710850609/EasyTier-EUI/releases/latest'
THROUGHPUT_TEST_BYTES = 64 * 1024         # 吞吐量测试下载字节数：64KB（Range: bytes=0-65535）
SUFFICIENT_PROXY_COUNT = 3                # 测速提前终止阈值：得到 N 个可用节点即停止
FALLBACK_PROXY_URLS = [
    'https://ghfast.top',
    'https://gh-proxy.com',
    'https://gh.llkk.cc',
]

# ── 线程本地 Session，复用 HTTP 连接 ──
_thread_local = threading.local()

def _get_thread_session() -> requests.Session:
    """获取当前线程的 requests.Session，自动创建并配置连接池"""
    if not hasattr(_thread_local, 'session'):
        s = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=4,
            pool_maxsize=8,
            max_retries=1,
        )
        s.mount('https://', adapter)
        s.mount('http://', adapter)
        _thread_local.session = s
    return _thread_local.session


class CdnError(Exception):
    """CDN/代理节点错误，不应重试当前 URL"""


def get_latest_version(api_url) -> str:
    """
    获取最新版本，如：https://api.github.com/repos/EasyTier/easytier-manager/releases/latest
    提取版本号 v1.2.3 -> 1.2.3
    """
    try:
        data = get_api(api_url)

        tag_name = data.get('tag_name', '')
        match = re.search(r'(\d+\.\d+\.\d+)', tag_name)
        if match:
            return match.group(1)
        raise ValueError(f"无法解析版本号: {tag_name}")
    except Exception as e:
        logger.error(f"获取 manager 版本失败: {e}")
        raise

def get_download_url_proxy(url: str) -> str:
    """获取 GitHub 代理 URL"""
    proxy_urls = get_proxy_urls()
    if proxy_urls and len(proxy_urls) > 0:
        proxy_url = proxy_urls[0]["url"]
        if proxy_url and proxy_url != '':
            logger.info(f"使用加速地址: {proxy_url}")
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
        session = _get_thread_session()
        response = session.get(request_url, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            return response.json()
        else:
            return response.content
    except requests.exceptions.RequestException as e:
        logger.warning(f"获取github文件HTTP异常: {str(e)}")
        if response and response.status_code == 404:
            logger.warning(f"文件不存在: {request_url}")
            raise e
        if proxy_url_list is None:
            proxy_urls = get_proxy_urls()
            if len(proxy_urls) > 0:
                proxy_url_list = [item["url"] for item in proxy_urls]
        if proxy_url_list and len(proxy_url_list) > 0:
            return download_raw_file(download_url, timeout, proxy_url_list)
        raise e

def get_api(url: str, proxy_url: str = ""):
    """获取 GitHub API 数据"""
    try:
        req_url = url
        if proxy_url and proxy_url != '':
            req_url = proxy_url + '/' + url
        session = _get_thread_session()
        response = session.get(req_url, timeout=10)
        if response.status_code == 404:
            raise HttpException(get_message('error.resource_not_found_at', url=req_url))
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"获取 API 数据失败: {e}")
        if not proxy_url or proxy_url == '':
            proxy_urls = get_proxy_urls()
            api_proxy_urls = [item['url'] for item in proxy_urls if item.get('supports_api', False)]
            if not api_proxy_urls:
                logger.error("无可用 API 加速地址，无法获取 GitHub API 数据")
                raise e
            for api_proxy_url in api_proxy_urls:
                logger.info(f"尝试使用 API 加速地址: {api_proxy_url}")
                try:
                    return get_api(url, api_proxy_url)
                except requests.exceptions.RequestException as e2:
                    logger.error(f"获取 API 数据失败: {e2}")
            raise e
        else:
            raise e

def get_proxy_urls(refresh:bool = False, progress_callback:Optional[Callable[[int, str], None]] = None, target_url:Optional[str] = None) -> list:
    """
    获取 GitHub 代理列表
    https://github.akams.cn/
    """
    current_lang = get_lang()
    proxy_file_path = Path(run_configs.data_dir(), 'github_proxy.json')
    cur_time = int(time.time() * 1000)
    if not refresh and proxy_file_path.exists() and not target_url:
        with open(proxy_file_path, 'r', encoding="utf-8") as f:
            cache_data = json.load(f)
            if cache_data and len(cache_data.get('sources', [])) > 0 and cur_time - cache_data.get('create_time', 0) < PROXY_CACHE_TTL_MS:
                logger.info(f"使用缓存代理列表: {cache_data.get('sources', [])}")
                return cache_data.get('sources', [])

    if progress_callback:
        progress_callback(0, get_message('github.getting_proxy_nodes', lang=current_lang))
    url_list = get_dns_txt_records(DNS_TXT_DOMAIN, timeout=DNS_TIMEOUT)
    if not url_list:
        logger.warning("DNS TXT 查询返回空，使用默认加速地址")
        url_list = list(FALLBACK_PROXY_URLS)
    logger.info(f"获取到GitHub 加速地址: {url_list}")
    url_list = [{'url': item} for item in url_list]
    url_list.append({'url': ''})  # 直连候选
    if progress_callback:
        progress_callback(0, get_message('github.checking_proxy_nodes', lang=current_lang))

    url_list = check_proxy_url(url_list, progress_callback=progress_callback, target_url=target_url)
    url_list = [item for item in url_list if item['status'] == 'ok']
    logger.debug(f"GitHub加速地址检测结果: {url_list}")

    if progress_callback:
        progress_callback(0, get_message('github.proxy_nodes_found', lang=current_lang, count=len(url_list)))
    if url_list and len(url_list) > 0:
        with open(proxy_file_path, 'w', encoding="utf-8") as f:
            f.write(json.dumps({'sources': url_list, 'create_time': cur_time}, indent=2))
    return url_list

def check_proxy_url(url_list:list, check_timeout:int = None, progress_callback=None, target_url:Optional[str] = None) -> list:
    """
    检查代理 URL 是否有效，同时检测文件下载和 API 访问支持。
    测速包含 HEAD 延迟 + 小文件下载吞吐量，得到 SUFFICIENT_PROXY_COUNT 个可用节点后提前终止。
    target_url: 要下载的目标 URL，自动判断类型：
        - 包含 'api.github.com' → 替换 API 测试 URL，文件测试仍用默认
        - 其他 → 替换文件测试 URL，API 测试仍用默认
        - 不传 → 两个都用默认测试 URL
    """
    if check_timeout is None:
        check_timeout = PROXY_CHECK_TIMEOUT
    workers = min(len(url_list), MAX_PROXY_CHECK_WORKERS)

    # ── 并发测速（含吞吐量测试）──
    def _test_speed(item):
        proxy = item["url"]
        result = {
            "url": proxy, "delay": -1, "throughput": 0,
            "status": "", "desc": "", "supports_range": False,
            "supports_api": False, "file_size": 0,
        }
        test_file_path = DEFAULT_TEST_FILE_URL
        test_api_path = DEFAULT_TEST_API_URL
        if target_url:
            if target_url.lower().startswith('https://api.github.com/'):
                test_api_path = target_url
            else:
                test_file_path = target_url
        test_file_url = f"{proxy}/{test_file_path}" if proxy else test_file_path
        test_api_url = f"{proxy}/{test_api_path}" if proxy else test_api_path

        start = time.time()
        try:
            test_headers = {"Range": "bytes=0-0"}
            session = _get_thread_session()
            resp = session.head(test_file_url, timeout=check_timeout, allow_redirects=True, headers=test_headers)
            if resp.status_code >= 400:
                result["status"] = f"http_{resp.status_code}"
                result["desc"] = f"不可用(HTTP {resp.status_code})"
                return result

            head_elapsed = time.time() - start
            result["delay"] = round(head_elapsed, 2)
            result["status"] = "ok"
            result["supports_range"] = (resp.status_code == 206)
            if resp.status_code == 206:
                content_range = resp.headers.get("Content-Range", "")
                if "/" in content_range:
                    result["file_size"] = int(content_range.split("/")[-1])
            else:
                result["file_size"] = int(resp.headers.get("Content-Length", 0))

            # ── 吞吐量测试：下载 64KB 测量实际传输速度 ──
            throughput_start = time.time()
            try:
                dl_headers = {"Range": f"bytes=0-{THROUGHPUT_TEST_BYTES - 1}"}
                dl_resp = session.get(test_file_url, headers=dl_headers, timeout=check_timeout * 2, stream=True)
                if dl_resp.status_code in (200, 206):
                    bytes_downloaded = 0
                    for chunk in dl_resp.iter_content(chunk_size=65536):
                        if chunk:
                            bytes_downloaded += len(chunk)
                    throughput_elapsed = time.time() - throughput_start
                    if throughput_elapsed > 0 and bytes_downloaded > 0:
                        result["throughput"] = round(bytes_downloaded / throughput_elapsed, 0)
                dl_resp.close()
            except requests.exceptions.RequestException:
                pass  # 吞吐量测试失败不影响节点可用性

            # API 支持检测
            try:
                api_resp = session.head(test_api_url, timeout=check_timeout, allow_redirects=True)
                result["supports_api"] = (api_resp.status_code == 200)
                api_resp.close()
            except requests.exceptions.RequestException:
                result["supports_api"] = False

        except requests.exceptions.Timeout:
            result["status"] = "timeout"
            result["desc"] = "超时"
        except Exception as e:
            result["status"] = str(e)
            result["desc"] = "不可用"
        return result

    # ── 并发执行，前 N 个可用后提前终止 ──
    url_list_out = []
    ok_count = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(_test_speed, item): idx for idx, item in enumerate(url_list)}
        try:
            for future in as_completed(future_map):
                result = future.result()
                url_list_out.append(result)
                if result["status"] == "ok":
                    ok_count += 1
                    if ok_count >= SUFFICIENT_PROXY_COUNT:
                        for f in future_map:
                            f.cancel()
                        break
        finally:
            for f in future_map:
                f.cancel()

    # ── 加权排序：可用优先 → 吞吐量降序 → 延迟升序 ──
    url_list_out.sort(key=lambda x: (
        x.get("status") != "ok",
        -(x.get("throughput", 0)),
        x.get("delay", -1) if x.get("delay", -1) > 0 else float('inf'),
    ))
    return url_list_out


def _download_chunk(
        url: str,
        start: int,
        end: int,
        part_path: Path,
        timeout: int = 120,
        max_retries: int = 2,
        chunk_progress_callback=None,
        reset_progress_callback=None
) -> bool:
    """
    下载文件的 [start, end] 字节段（两端闭合）。
    失败会自动重试，返回是否成功。
    """
    headers = {"Range": f"bytes={start}-{end}"}
    session = _get_thread_session()

    for attempt in range(max_retries + 1):
        if reset_progress_callback:
            reset_progress_callback()
        try:
            with session.get(url, headers=headers, stream=True, timeout=timeout) as resp:
                if resp.status_code not in (200, 206):
                    if resp.status_code >= 500:
                        raise CdnError(f"CDN节点错误 HTTP {resp.status_code}")
                    raise Exception(f"HTTP {resp.status_code}")

                with open(part_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            if chunk_progress_callback:
                                chunk_progress_callback(len(chunk))

                content_type = resp.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    if part_path.exists():
                        part_path.unlink(missing_ok=True)
                    raise CdnError(f"返回了 HTML 页面而非文件: Content-Type={content_type}")

                return True
        except CdnError:
            logger.warning(f"分片下载失败 [{start}-{end}] CDN 错误，不重试")
            if part_path.exists():
                part_path.unlink(missing_ok=True)
            return False
        except Exception as e:
            logger.warning(f"分片下载失败 [{start}-{end}] 第{attempt + 1}次: {e}")
            if part_path.exists():
                part_path.unlink(missing_ok=True)
            if "HTTP 5" in str(e) and attempt == 0:
                return False

    return False


def download_release_file(
        download_url: str,
        output_path: str,
        desc: str = "",
        num_threads: int = 4,
        timeout: int = 300,
        progress_callback:Optional[Callable[[int, str], None]] = None
) -> None:
    """
    多镜像 + 分段并行下载，支持并发下载同一文件（下载到 temp 目录，完成后原子移动）。

    :param download_url: GitHub 下载地址
    :param output_path: 最终保存路径
    :param desc: 进度描述
    :param num_threads: 分段并行数，默认 4
    :param timeout: 请求超时时间，默认 300 秒
    :param progress_callback: 进度回调 callback(percent: int, description: str)
    """
    current_lang = get_lang()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 所有分片下载到临时目录，保证并发不冲突，原子移动到最终路径
    temp_dir = output_path.parent / 'temp' / f'{uuid.uuid4().hex[:8]}'
    temp_dir.mkdir(parents=True, exist_ok=True)
    check_result = get_proxy_urls(refresh=True, progress_callback=progress_callback, target_url=download_url)

    # ========== 1. 探测可用 URL 和文件大小 ==========
    usable_urls = []
    usable_range_urls = []
    for item in check_result:
        if item.get('delay') >= 0:
            proxy = item.get('url', '')
            url = proxy + '/' + download_url if proxy else download_url
            usable_urls.append(url)
            if item.get('supports_range', False):
                usable_range_urls.append(url)
    if not usable_urls:
        raise Exception("所有下载地址均不可用（代理+直连）")

    # 优先用支持 Range 的地址进行分段下载
    if not usable_range_urls:
        # 全都不支持 Range，回退到单线程，挑第一个可用的
        logger.warning("没有地址支持 Range，回退到单线程下载")
        _download_single(usable_urls[0], temp_dir / output_path.name, desc, timeout, progress_callback=progress_callback, lang=current_lang)
        shutil.move(str(temp_dir / output_path.name), str(output_path))
        return
    
    # 获取文件大小：检测阶段已经得到，优先取第一个非零值
    total_size = 0
    for item in check_result:
        total_size = item.get('file_size', 0)
        if total_size > 0:
            break
    if total_size == 0:
        logger.info("检测阶段未获取到文件大小，回退到逐个 HEAD 探测")
        session = _get_thread_session()
        validated_range_urls = []
        for url in usable_range_urls:
            resp = session.head(url, allow_redirects=True, timeout=timeout)
            if resp.status_code < 400:
                total_size = int(resp.headers.get("content-length", 0))
                validated_range_urls.append(url)
            else:
                logger.warning(f"HEAD 请求失败 {url}: HTTP {resp.status_code}，跳过该地址")
        if not validated_range_urls:
            raise Exception(f"所有支持 Range 的下载地址 HEAD 请求均失败，请更换网络环境")
        usable_range_urls = validated_range_urls
    else:
        logger.info(f"检测阶段已获取文件大小: {total_size} 字节")
    
    logger.info(f"加速地址可用 {len(usable_urls)} 个，支持 Range 下载 {len(usable_range_urls)} 个")

    # ========== 2. 小文件跳过并行下载，减少不必要的开销 ==========
    if 0 < total_size < SMALL_FILE_THRESHOLD:
        logger.info(f"文件较小({total_size}字节)，跳过并行下载")
        _download_single(usable_range_urls[0] if usable_range_urls else usable_urls[0],
                         temp_dir / output_path.name, desc, timeout,
                         progress_callback=progress_callback, lang=current_lang)
        shutil.move(str(temp_dir / output_path.name), str(output_path))
        return

    # ========== 3. 计算分片 ==========
    chunk_size = max(total_size // num_threads, MIN_CHUNK_SIZE)

    chunks: List[Tuple[int, int, Path]] = []
    for i in range(0, total_size, chunk_size):
        start = i
        end = min(i + chunk_size - 1, total_size - 1)  # Range 是闭合区间
        part_path = temp_dir / f"{output_path.name}.part_{start}_{end}"
        chunks.append((start, end, part_path))

    logger.info(f"{desc} 分片信息: {len(chunks)} 段, 总大小: {total_size}")

    # ========== 3. 并行下载（带故障转移） ==========
    progress_lock = threading.Lock()
    chunk_progress = {}  # {(start, end): bytes_downloaded}
    last_percent = [-1]

    def _download_with_fallback(start: int, end: int, part_path: Path) -> bool:
        """尝试所有可用 URL 下载该分片"""
        # 优先用 Range 支持的 URL，失败再试其他
        candidates = usable_range_urls + [u for u in usable_urls if u not in usable_range_urls]
        chunk_key = (start, end)

        def on_chunk_received(chunk_size):
            with progress_lock:
                chunk_progress[chunk_key] = chunk_progress.get(chunk_key, 0) + chunk_size
                current = sum(chunk_progress.values())
                if total_size > 0:
                    p = int(current / total_size * 100)
                    if p > last_percent[0]:
                        logger.info(f"{desc} 分片下载进度: {p}%")
                        last_percent[0] = p
                        if progress_callback:
                            progress_callback(p, get_message('github.chunk_download_progress', lang=current_lang, percent=p))

        for url in candidates:
            logger.debug(f"尝试下载 [{start}-{end}] from {url}")
            chunk_progress[chunk_key] = 0
            if _download_chunk(url, start, end, part_path, timeout=timeout, chunk_progress_callback=on_chunk_received, reset_progress_callback=lambda: chunk_progress.update({chunk_key: 0})):
                with progress_lock:
                    chunk_progress[chunk_key] = end - start + 1
                return True
            logger.warning(f"URL 失败，切换镜像: {url}")

        # 所有镜像均失败，清零该分片的进度
        with progress_lock:
            chunk_progress[chunk_key] = 0
        return False

    failed = False
    try:
        with ThreadPoolExecutor(max_workers=num_threads, initializer=set_lang, initargs=(current_lang,)) as executor:
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

        # ========== 4. 合并前校验分片完整性 ==========
        for start, end, part_path in chunks:
            if not part_path.exists():
                raise Exception(f"分片文件缺失: {part_path.name}")
            expected_size = end - start + 1
            actual_size = part_path.stat().st_size
            if actual_size != expected_size:
                raise Exception(f"分片文件大小不匹配: {part_path.name}, 期望 {expected_size}, 实际 {actual_size}")

        # ========== 5. 合并文件 ==========
        logger.info(f"{desc} 下载完成，开始合并...")
        temp_file = temp_dir / output_path.name
        with open(temp_file, "wb") as outfile:
            for start, end, part_path in chunks:
                with open(part_path, "rb") as infile:
                    outfile.write(infile.read())
                part_path.unlink(missing_ok=True)

        logger.info(f"{desc} 合并完成: {temp_file}")

        final_size = temp_file.stat().st_size
        if total_size > 0 and final_size != total_size:
            raise Exception(f"合并后文件大小不匹配: 期望 {total_size} 字节, 实际 {final_size} 字节")

        shutil.move(str(temp_file), str(output_path))
        logger.info(f"{desc} 已移动到: {output_path}")

    except Exception:
        # 清理残片
        for _, _, part_path in chunks:
            part_path.unlink(missing_ok=True)
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(str(temp_dir), ignore_errors=True)


def _download_single(url: str, output_path: Path, desc: str, timeout: int, progress_callback:Optional[Callable[[int, str], None]] = None, lang: str = None):
    """不支持 Range 时的单线程回退"""
    if lang is None:
        lang = get_lang()
    logger.info(f"{desc} 单线程下载: {url}")
    session = _get_thread_session()
    with session.get(url, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        content_type = resp.headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            raise Exception(f"返回了 HTML 页面而非文件: Content-Type={content_type}")
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
                                logger.info(f"{desc} 单线程下载进度: {p}%")
                                progress_callback(p, get_message('github.single_download_progress', lang=lang, percent=p))
    logger.info(f"{desc} 下载完成")