#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import atexit
import json
import logging
import os
import sys
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Optional

import psutil

from http_dispatcher import dispatcher
from utils import run_configs, log_util, ip_util, qrcode_util, permissions_util

BASE_URI = "/cgi/ThirdParty/EasyTier-EUI/index.cgi"

class CGIProxyHandler(BaseHTTPRequestHandler):
    """处理 HTTP 请求并转发给 CGI 脚本"""
    def log_message(self, format, *args):
        if sys.stdout is None:
            return
        logging.debug("[%s] - %s\n" %
                         (self.address_string(),
                          format % args))

    def do_GET(self):
        """处理 GET 请求"""
        self.handle_request()

    def do_POST(self):
        """处理 POST 请求"""
        self.handle_request()

    def handle_request(self):
        """处理请求的核心逻辑"""
        try:
            # 解析请求路径
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            # 构建完整的 REQUEST_URI
            request_uri = path
            if parsed_path.query:
                request_uri = f"{path}?{parsed_path.query}"
            self.run_cgi(parsed_path.query, request_uri)

        except Exception as e:
            logging.error(f"Request handling error: {e}", exc_info=True)
            self.send_error(500, f"Internal server error: {str(e)}")

    def run_cgi(self, query_string, request_uri):
        """执行 CGI 脚本并返回结果"""
        try:
            # 获取请求体（POST 请求）
            stdin_data = None
            content_length = self.headers.get('Content-Length')
            if self.command == 'POST' and content_length:
                try:
                    content_length = int(content_length)
                    if content_length > 0:
                        stdin_data = self.rfile.read(content_length)
                except ValueError:
                    pass

            # 构建环境变量
            env = os.environ.copy()
            env.update({
                'REQUEST_METHOD': self.command,
                'QUERY_STRING': query_string,
                'REQUEST_URI': request_uri,
                'SERVER_PROTOCOL': self.request_version,
                'SERVER_NAME': self.headers.get('Host', 'localhost').split(':')[0],
                'SERVER_PORT': str(self.server.server_port),
                'CONTENT_TYPE': self.headers.get('Content-Type', ''),
                'CONTENT_LENGTH': str(content_length) if content_length else '',
                'HTTP_HOST': self.headers.get('Host', ''),
                'HTTP_USER_AGENT': self.headers.get('User-Agent', ''),
                'HTTP_ACCEPT': self.headers.get('Accept', ''),
                'HTTP_ACCEPT_ENCODING': self.headers.get('Accept-Encoding', ''),
                'HTTP_ACCEPT_LANGUAGE': self.headers.get('Accept-Language', ''),
                'HTTP_COOKIE': self.headers.get('Cookie', ''),
                'HTTP_REFERER': self.headers.get('Referer', ''),
                'HTTP_X_FORWARDED_FOR': self.headers.get('X-Forwarded-For', ''),
                'HTTP_X_REAL_IP': self.headers.get('X-Real-IP', ''),
            })

            # 添加所有以 HTTP_ 开头的自定义头
            for header, value in self.headers.items():
                header_key = f"HTTP_{header.upper().replace('-', '_')}"
                if header_key not in env:
                    env[header_key] = value

            # 保存原始环境变量，避免污染全局环境
            original_env = os.environ.copy()
            try:
                # 临时设置环境变量供 dispatcher 使用
                os.environ.update(env)
                resp = dispatcher.http_handle(base_uri=BASE_URI, body_data=stdin_data, cgi_module=False)
            finally:
                # 恢复原始环境变量
                os.environ.clear()
                os.environ.update(original_env)
            self.send_response(resp.status_code)
            if resp.headers is not None:
                for key, value in resp.headers.items():
                    self.send_header(key, value)
            self.end_headers()
            # 发送内容
            if resp.file:
                with open(resp.file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(json.dumps(resp.json, ensure_ascii=False, indent=2).encode())

        except Exception as e:
            logging.error(f"CGI execution error: {e}", exc_info=True)
            self.send_error(500, f"CGI execution error: {str(e)}")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """支持多线程的 HTTP 服务器"""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        # 你自己的初始化代码（可选）
        super().__init__(server_address, RequestHandlerClass)
        # 也可以在这里做其他初始化

def _acquire_instance_lock() -> bool:
    """获取单实例锁（PID 文件），失败则说明已有实例在运行"""
    pid_file = os.path.join(run_configs.data_dir(), 'server.pid')
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                existing_pid = int(f.read().strip())
            if psutil.pid_exists(existing_pid):
                return False
            else:
                os.remove(pid_file)
        except (ValueError, OSError):
            os.remove(pid_file)

    os.makedirs(os.path.dirname(pid_file), exist_ok=True)
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    return True


def _release_instance_lock():
    """释放单实例锁"""
    pid_file = os.path.join(run_configs.data_dir(), 'server.pid')
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            if pid == os.getpid():
                os.remove(pid_file)
        except (ValueError, OSError):
            pass

def build(host:str, port:int=5666, open_browser:bool=False) -> Optional[ThreadedHTTPServer]:
    """启动 HTTP 服务器"""
    logging.info(f"运行的构建版本：{run_configs.build_version()}")

    if not _acquire_instance_lock():
        logging.warning(f"HTTP 服务已在运行中，不能重复启动")
        return None
    atexit.register(_release_instance_lock)

    if not host:
        host = '0.0.0.0'
    if host == '0.0.0.0' and run_configs.get_run_mode() == 0:
        # 优化本地启动速度，默认绑定 127.0.0.1
        host = '127.0.0.1'
    logging.info(f"HTTP服务启动中....")
    http_server = ThreadedHTTPServer((host, port), CGIProxyHandler)
    logging.info(f"Starting HTTP server on {host}, port: {port}")
    logging.info(f"Virtual base URI: {BASE_URI}")
    acc_host = http_server.server_address[0]
    acc_port = http_server.server_address[1]
    if acc_host == '0.0.0.0':
        lan_ips = ip_util.get_lan_ips()
        acc_host = lan_ips[0].get('ip') if len(lan_ips) > 0 else '127.0.0.1'
    access_url = f"http://{acc_host}:{acc_port}"
    qr_code = qrcode_util.create_str(access_url)
    logging.info(f"Access URL {access_url} , QrCode: {qr_code}")
    if open_browser:
        try:
            webbrowser.open_new_tab(access_url)
            logging.info(f"已打开本地设备浏览器，请在浏览器上访问")
        except Exception as e:
            logging.error(f"打开本地设备不支持浏览器访问: {e}")
    return http_server

def serve_forever(http_server:ThreadedHTTPServer) -> None:
    """启动 HTTP 服务器"""
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        http_server.shutdown()
    finally:
        _release_instance_lock()


if __name__ == '__main__':
    permissions_util.elevate()
    run_configs.setup_env()
    run_mode = run_configs.get_run_mode()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'),
                       log_level=logging.INFO if run_mode > 0 else logging.DEBUG,
                       enabled_console=run_mode == 0)
    import argparse
    parser = argparse.ArgumentParser(description='CGI Proxy HTTP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5666, help='Port to bind to (default: 5666)')
    args = parser.parse_args()
    http_server = build(args.host, args.port, open_browser=run_mode == 1)
    if http_server:
        serve_forever(http_server)
    else:
        sys.exit(1)