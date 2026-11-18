#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import atexit
import faulthandler
import logging
import os
import sys
import threading
import time
from typing import Optional

from actions import services
from http_dispatcher import http_server
from utils import run_configs, log_util, permissions_util, ip_util, qrcode_util
from utils.permissions_util import ServerHandle

logger = logging.getLogger(__name__)
BASE_URI = "/cgi/ThirdParty/EasyTier-EUI/index.cgi"

# 崩溃守护 / stderr 重定向的文件句柄，stop_server 时统一释放
_faulthandler_file = None
_stderr_file = None


def start_server(host: str = None, port: int = None) -> dict:
    """统一启动入口：前置处理 → 启动 HTTP → 后置处理。

    - 前置：初始化环境、日志、错误处理
    - 启动：提权判定 + 检查是否已启动 + 启动 HTTP
    - 后置：docker 启动核心服务 / stun 自启 / Android 恢复最近网络
    - 返回 {'handle': ServerHandle, 'port': int}，port 为服务实际监听端口。
    """
    # 1. 前置处理
    init_env()

    # 2. 启动 HTTP 服务
    handle = _start_http(host, port, exit_on_failure=True)
    if handle is None:
        sys.exit(1)

    # 3. 后置处理
    _post_setup()

    actual_port = handle._server.server_address[1] if handle._server is not None else port
    actual_host = handle._server.server_address[0] if handle._server is not None else host
    return {"handle": handle, "host": actual_host, "port": actual_port}


def init_env() -> None:
    """初始化运行环境：环境、日志、错误处理。
    平台路径由环境变量注入（Android 端 ANDROID_DATA_DIR / ANDROID_EXTERNAL_DIR 由 Kotlin 注入）。
    不启动 HTTP 服务器，供服务启动前初始化路径使用。"""
    run_configs.setup_env()
    run_mode = run_configs.get_run_mode()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'),
                       log_level=logging.DEBUG if run_mode == 0 else None,
                       enabled_console=run_mode == 0 or run_configs.is_docker())
    _setup_crash_guard()
    _redirect_stderr()


def _post_setup():
    """后置处理：Android 恢复最近网络；桌面 docker 启动核心服务 + stun 自启。"""
    if run_configs.IS_ANDROID:
        threading.Thread(target=services.start_all, daemon=True, name='async-vpn-startup').start()
    elif run_configs.is_docker():
        services.start_all()
    from actions import stun
    stun.start_enable()


def stop_server(handle: ServerHandle, port: int):
    """统一停止入口：停止 HTTP 服务 + 关闭崩溃守护 / stderr 文件。"""
    _stop_http(handle, port)
    _close_guards()


def _setup_crash_guard():
    global _faulthandler_file
    if _faulthandler_file is not None:
        return
    crash_log = os.path.join(run_configs.log_dir(), 'python_crash.log')
    _rotate_file(crash_log)
    try:
        _faulthandler_file = open(crash_log, 'a', buffering=1)
        faulthandler.enable(file=_faulthandler_file, all_threads=True)
        logger.debug(f"faulthandler enabled, crash log: {crash_log}")
    except Exception as fe:
        logger.debug(f"faulthandler enable failed: {fe}")


def _redirect_stderr():
    global _stderr_file
    if _stderr_file is not None:
        return
    if run_configs.get_run_mode() == 0 or run_configs.is_docker():
        return
    stderr_log = os.path.join(run_configs.log_dir(), 'python_stderr.log')
    try:
        _stderr_file = _RotatingFile(stderr_log)
        sys.stderr = _stderr_file
        logger.debug(f"stderr redirected to: {stderr_log}")
    except Exception as se:
        logger.debug(f"stderr redirect failed: {se}")


def _close_guards():
    global _faulthandler_file, _stderr_file
    try:
        faulthandler.disable()
    except Exception:
        pass
    for f in (_faulthandler_file, _stderr_file):
        if f is not None:
            try:
                f.close()
            except Exception:
                pass
    _faulthandler_file = None
    _stderr_file = None


atexit.register(_close_guards)


def _rotate_file(filepath, max_size=5 * 1024 * 1024, backups=1):
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) >= max_size:
            for i in range(backups - 1, 0, -1):
                src = f"{filepath}.{i}"
                dst = f"{filepath}.{i + 1}"
                if os.path.exists(src):
                    if os.path.exists(dst):
                        os.remove(dst)
                    os.rename(src, dst)
            bak = f"{filepath}.1"
            if os.path.exists(bak):
                os.remove(bak)
            os.rename(filepath, bak)
    except Exception:
        pass


class _RotatingFile:
    def __init__(self, filepath, max_size=5 * 1024 * 1024, backups=1):
        self.filepath = filepath
        self.max_size = max_size
        self.backups = backups
        self._fd = open(filepath, 'a', buffering=1)

    def write(self, data):
        if self._fd.tell() >= self.max_size:
            self._fd.close()
            _rotate_file(self.filepath, self.max_size, self.backups)
            self._fd = open(self.filepath, 'a', buffering=1)
        self._fd.write(data)
        self._fd.flush()

    def flush(self):
        self._fd.flush()

    def close(self):
        self._fd.close()

    def fileno(self):
        return self._fd.fileno()


def _start_http(host: str, port: int, exit_on_failure: bool = False) -> Optional[ServerHandle]:
    """启动 HTTP 服务：提权判定 + 检查是否已启动 + 启动。返回 ServerHandle。"""
    host = host or run_configs.EUI_RUN_HOST or '0.0.0.0'
    port = port or run_configs.EUI_RUN_PORT or 5666
    if not run_configs.IS_ANDROID and not permissions_util.is_admin():
        try:
            handle = permissions_util.run_elevated_module(
                'http_dispatcher.http_server', args=[f'--host={host}', f'--port={port}', f'--base_uri={BASE_URI}'])
            if handle is None:
                logger.error("提权进程启动失败，返回 None")
                if exit_on_failure:
                    sys.exit(1)
                return None
            logger.info(f"提权进程已启动 PID={handle.pid}")
            return handle
        except Exception as e:
            logger.exception(f"提权启动异常: {e}")
            if exit_on_failure:
                sys.exit(1)
            return None
    else:
        logger.info(f"当前用户已是管理员权限")
        server = http_server.build(host, port, BASE_URI)
        if server is None:
            logger.error("HTTP 服务启动失败")
            if exit_on_failure:
                sys.exit(1)
            return None
        threading.Thread(target=http_server.serve_forever, args=(server,), daemon=True, name='http-server').start()
        logger.info(f"HTTP 服务已在后台线程启动")
        return ServerHandle(server=server)


def _stop_http(handle: ServerHandle, port: int):
    import urllib.request
    try:
        url = f'http://127.0.0.1:{port}{BASE_URI}/api/settings/shutdown'
        logger.info(f"尝试通过 HTTP 请求关闭提权进程: {url}")
        req = urllib.request.Request(
            url, data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=3)
        logger.info("已通过 HTTP 请求关闭提权进程")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"HTTP 关闭请求失败: {e}")
    finally:
        if handle._server is not None:
            try:
                handle.stop()
                logger.info("已通过 handle.stop() 停止服务")
            except Exception:
                pass




if __name__ == '__main__':
    import signal
    import webbrowser
    import argparse

    permissions_util.handle_elevated_run()
    run_configs.setup_env()
    run_mode = run_configs.get_run_mode()

    parser = argparse.ArgumentParser(description='CGI Proxy HTTP Server')
    parser.add_argument('--host', help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to bind to')
    parser.add_argument('--base_uri', default=BASE_URI, help=f'Base URI to use (default: {BASE_URI})')
    args = parser.parse_args()

    BASE_URI = args.base_uri
    host = args.host
    port = args.port

    result = start_server(host, port)
    handle = result["handle"]
    port = result["port"]
    host = result["host"]

    _shutdown_requested = False

    def _on_sigint(signum, frame):
        global _shutdown_requested
        _shutdown_requested = True

    original_sigint = signal.signal(signal.SIGINT, _on_sigint)

    try:
        acc_host = host
        acc_port = port
        if acc_host == '0.0.0.0':
            if run_mode == 0:
                acc_host = '127.0.0.1'
            else:
                lan_ips = ip_util.get_lan_ips()
                acc_host = lan_ips[0].get('ip') if len(lan_ips) > 0 else '127.0.0.1'
        access_url = f"http://{acc_host}:{acc_port}"
        qr_code = qrcode_util.create_str(access_url)
        logger.info(f"访问地址: {access_url} , QrCode: {qr_code}")
        time.sleep(1)
        if run_mode != 0:
            webbrowser.open_new_tab(access_url)
            logger.info(f"已打开本地设备浏览器，请在浏览器上访问")
    except Exception as e:
        logger.error(f"打开本地设备不支持浏览器访问: {e}")

    try:
        logger.info("按 Ctrl+C 停止服务")
        while not _shutdown_requested:
            time.sleep(1)
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        try:
            stop_server(handle, port)
        except KeyboardInterrupt:
            pass