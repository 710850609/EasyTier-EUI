#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Optional

from http_dispatcher import dispatcher
from utils import run_configs, log_util

BASE_URI = "/cgi/ThirdParty/EasyTier-Lite/index.cgi"

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

            for item in env.items():
                os.environ[item[0]] = item[1]

            resp = dispatcher.http_handle(base_uri=BASE_URI, body_data=stdin_data, cgi_module=False)
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

def build_server(host='127.0.0.1', port=5666, base_uri=None) -> Optional[ThreadedHTTPServer]:
    """启动 HTTP 服务器"""
    logging.info(f"HTTP服务启动中....")
    server = ThreadedHTTPServer((host, port), CGIProxyHandler)
    logging.info(f"Starting HTTP server on {host}:{port}")
    logging.info(f"Virtual base URI: {BASE_URI}")
    acc_host = host
    if acc_host == '0.0.0.0':
        acc_host = '127.0.0.1'
    logging.info(f"local access http://{acc_host}:{port}{BASE_URI}")
    return server


if __name__ == '__main__':
    run_configs.setup_env()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'), log_level=logging.DEBUG,
                       enabled_console=True)
    import argparse
    parser = argparse.ArgumentParser(description='CGI Proxy HTTP Server')
    # parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5666, help='Port to bind to (default: 5666)')
    args = parser.parse_args()

    server = build_server(args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        server.shutdown()