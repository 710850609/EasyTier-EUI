#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import atexit
import json
import logging
import os
import signal
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from time import sleep
from typing import Optional

import psutil

from http_dispatcher import dispatcher
from utils import run_configs, log_util

class CGIProxyHandler(BaseHTTPRequestHandler):
    """处理 HTTP 请求并转发给 CGI 脚本"""

    base_uri = ''  # 默认值，build() 时可覆盖

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

            # 只覆盖 dispatcher 需要的 CGI 变量，避免全量 copy/clear/update
            cgi_env_keys = {
                'REQUEST_METHOD', 'QUERY_STRING', 'REQUEST_URI', 'SERVER_PROTOCOL',
                'SERVER_NAME', 'SERVER_PORT', 'CONTENT_TYPE', 'CONTENT_LENGTH',
                'HTTP_HOST', 'HTTP_USER_AGENT', 'HTTP_ACCEPT', 'HTTP_ACCEPT_ENCODING',
                'HTTP_ACCEPT_LANGUAGE', 'HTTP_COOKIE', 'HTTP_REFERER',
                'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP',
            }
            backup = {}
            for key in cgi_env_keys:
                backup[key] = os.environ.get(key)
            os.environ.update(env)
            for header, value in self.headers.items():
                header_key = f"HTTP_{header.upper().replace('-', '_')}"
                if header_key not in env:
                    env[header_key] = header_key
                    backup[header_key] = os.environ.get(header_key)
                    os.environ[header_key] = value
            try:
                resp = dispatcher.http_handle(base_uri=self.base_uri, body_data=stdin_data, cgi_module=False)
            finally:
                for key, original_value in backup.items():
                    if original_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = original_value
            self.send_response(resp.status_code)
            if resp.headers is not None:
                for key, value in resp.headers.items():
                    self.send_header(key, value)
            self.end_headers()
            # 发送内容
            if resp.file:
                with open(resp.file, "rb") as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
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
        super().__init__(server_address, RequestHandlerClass)


def _acquire_instance_lock(force_boot:bool) -> bool:
    """获取单实例锁（PID 文件），失败则说明已有实例在运行"""
    pid_file = os.path.join(run_configs.data_dir(), 'server.pid')
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                existing_pid = int(f.read().strip())
            if psutil.pid_exists(existing_pid):
                logging.warning(f"HTTP 服务已在运行中，{pid_file} 【{existing_pid}】")
                p = psutil.Process(existing_pid)
                if force_boot:
                    cmdline = ' '.join(p.cmdline())
                    logging.warning(f"强制启动 HTTP 服务，停止先前运行实例： 【{cmdline}】")
                    p.terminate()
                    try:
                        p.wait(timeout=1)
                    except psutil.TimeoutExpired:
                        p.kill()
                        p.wait()
                    except psutil.NoSuchProcess:
                        pass
                    os.remove(pid_file)
                    return True
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

def build(host:str, port:int=5666, base_uri: str = '', force_boot:bool=False) -> Optional[ThreadedHTTPServer]:
    """构建 HTTP 服务器，不阻塞。由调用方调用 serve_forever() 进入事件循环"""
    try:
        if not _acquire_instance_lock(force_boot):
            logging.warning(f"HTTP 服务已在运行中，不能重复启动")
            return None
        atexit.register(_release_instance_lock)

        logging.info(f"运行的构建版本：{run_configs.build_version()}")
        if not host:
            host = '0.0.0.0'
        if host == '0.0.0.0' and run_configs.get_run_mode() == 0:
            # win本地开发模式下，默认绑定到 127.0.0.1，优化启动速度
            host = '127.0.0.1'
        logging.info(f"HTTP服务启动中....")
        CGIProxyHandler.base_uri = base_uri
        server = ThreadedHTTPServer((host, port), CGIProxyHandler)
        logging.info(f"Starting HTTP server on {host}, port: {port}")
        # logging.info(f"Virtual base URI: {BASE_URI}")
        return server
    except Exception as e:
        logging.error(f"HTTP 服务启动失败: {e}")
        raise e

def serve_forever(http_server:ThreadedHTTPServer) -> None:
    """启动 HTTP 服务器事件循环"""
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        http_server.shutdown()
    finally:
        _release_instance_lock()

def start(host:str, port:int, base_uri: str) -> None:
    """启动 HTTP 服务器"""
    server = build(host, port, base_uri)
    if server:
        serve_forever(server)
    else:
        sys.exit(1)

if __name__ == '__main__':
    run_configs.setup_env()
    run_mode = run_configs.get_run_mode()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'),
                       log_level=logging.INFO if run_mode > 0 else logging.DEBUG,
                       enabled_console=run_mode == 0)
    import argparse
    parser = argparse.ArgumentParser(description='CGI Proxy HTTP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5666, help='Port to bind to (default: 5666)')
    parser.add_argument('--base_uri', default='', help='Base URI for virtual requests (default: empty)')
    args = parser.parse_args()
    start(args.host, args.port, args.base_uri)
