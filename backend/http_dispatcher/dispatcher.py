#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGI模式实现，兼容飞牛CGI应用和普通http服务
"""
import importlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from urllib.parse import unquote


class HttpException(Exception):

    def __init__(self, message, status_code=200, headers=None):
        self.status_code = status_code
        self.message = message
        self.headers = headers

class HttpRequest:

    def __init__(self, method, request_uri, resource_uri, headers=None, query_string=None, request_body=None,
                 module_name=None, function_name=None, function_params=None):
        self.method = method
        self.request_uri = request_uri
        self.resource_uri = resource_uri
        self.headers = headers
        self.query_string = query_string
        self.request_body = request_body
        self.module_name = module_name
        self.function_name = function_name
        self.function_params = self.__build_fun_params()
        pass

    def __build_fun_params(self):
        fun_params = None
        if self.request_body:
            try:
                fun_params = json.loads(self.request_body)
            except json.JSONDecodeError:
                fun_params = None
        query_params = {}
        if self.query_string:
            for param in self.query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    query_params[unquote(key)] = unquote(value)
            if fun_params is None:
                fun_params = query_params
            else:
                fun_params.update(query_params)
        return fun_params

class HttpResponse(Exception):
    def __init__(self, code=0, data=None, file: Optional[str]=None, mime_type=None, download_name:str=None, status_code=200, headers=None):
        if data and file:
            raise AssertionError(f"不能同时存在data和file")
        self.code = code
        self.status_code = status_code
        self.headers = headers or {}
        self.data = data
        self.json = {'code': self.code, 'data': self.data} if file is None else None
        self.file = file
        self.download_name = download_name
        self.mime_type = mime_type

    def _get_file_disposition(self):
        # 检查文件
        if not self.download_name:
            return None
        disposition = None
        if Path(self.file).is_file():
            # 文件名处理
            filename = self.download_name
            if not filename:
                filename = os.path.basename(self.file)

            # RFC 5987 编码（只编码非 ASCII）
            try:
                filename.encode('ascii')
                # 纯 ASCII，简单处理
                disposition = f'attachment; filename="{filename}"'
            except UnicodeEncodeError:
                # 含中文，需要编码
                encoded = quote(filename, safe='')
                # 同时提供 filename 和 filename* 兼容所有浏览器
                ascii_name = filename.encode('ascii', 'ignore').decode().replace('"', '')
                disposition = f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'
        return disposition

    def fill_headers(self):
        if self.headers is None:
            self.headers = {}
        
        # 添加 CORS 头
        self.headers['Access-Control-Allow-Origin'] = '*'
        self.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        self.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        self.headers['Access-Control-Max-Age'] = '86400'
        
        if self.file:
            mime_type = self.mime_type
            if not mime_type:
                ext = self.file.split(".")[-1].lower()
                mime_map = {
                    "html": "text/html; charset=utf-8",
                    "css": "text/css; charset=utf-8",
                    "js": "application/javascript; charset=utf-8",
                    "json": "application/json; charset=utf-8",
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "gif": "image/gif",
                    "svg": "image/svg+xml",
                    "woff": "font/woff",
                    "woff2": "font/woff2",
                }
                mime_type = mime_map.get(ext, "application/octet-stream")
            # 文件大小
            file_size = os.path.getsize(self.file)
            self.headers['Content-Length'] = file_size
            self.headers['Content-Type'] = mime_type
            disposition = self._get_file_disposition()
            if disposition:
                self.headers['Content-Disposition'] = disposition
        else:
            self.headers['Content-Type'] = 'application/json; charset=utf-8'
        return self.headers


    def output_cgi(self):
        sys.stdout.buffer.write(f"Status: {self.status_code}\r\n".encode())
        for h_key, h_value in self.headers.items():
            sys.stdout.buffer.write(f"{h_key}: {h_value}\r\n".encode())
        sys.stdout.buffer.write("\r\n".encode())
        if self.json:
            sys.stdout.buffer.write(json.dumps(self.json, ensure_ascii=False).encode())
        else:
            # 流式发送文件
            try:
                with open(self.file, "rb") as f:
                    while True:
                        chunk = f.read(65536)  # 64KB 块
                        if not chunk:
                            break
                        sys.stdout.buffer.write(chunk)
                        sys.stdout.buffer.flush()
            except BrokenPipeError:
                pass  # 客户端断开
            except Exception as e:
                logging.error(f"Send file error: {e}\n")
                sys.stderr.write(f"Send file error: {e}\n")


    def to_json(self):
        """返回一个可被 json.dumps 序列化的字典"""
        return json.dumps(self.json, ensure_ascii=False)


def get_request(base_uri="", body_data=None, cgi_module=True) -> HttpRequest:
    # 从环境变量获取http请求参数
    method = os.environ.get('REQUEST_METHOD', '')
    request_uri = os.environ.get('REQUEST_URI', '')
    query_string = os.environ.get('QUERY_STRING', '')

    if not request_uri.startswith(base_uri):
        # 统一一份前端打包，自动重定向到合适飞牛的固定前置
        logging.info(f"重定向到基础请求路径：{base_uri}")
        raise HttpException(f"请求地址必须以{base_uri}开头", status_code=302, headers={'Location': base_uri})
    uri = request_uri
    if base_uri != '/':
        uri = request_uri.replace(base_uri, '')
    uri_path = uri.split("?", 1)[0].split('/')[1:]

    content_type = os.environ.get('CONTENT_TYPE', '')
    content_length_str = os.environ.get('CONTENT_LENGTH', '0')
    content_length = int(content_length_str) if content_length_str else 0

    request_body = None
    if not cgi_module and body_data:
        request_body = body_data.decode()

    if cgi_module and content_length > 0:
        request_body = sys.stdin.read(content_length)

    request_data = None
    if request_body:
        try:
            request_data = json.loads(request_body)
        except json.JSONDecodeError:
            request_data = None

    query_params = {}
    if query_string:
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value
        if request_data is None:
            request_data = query_params
        else:
            request_data.update(query_params)

    module_name = None
    function_name = None
    if len(uri_path) == 3 and uri_path[0] == 'api':
        module_name = f"actions.{uri_path[1]}"
        function_name = uri_path[2]
    return HttpRequest(method=method, request_uri=request_uri, resource_uri = '/'.join(uri_path),
                       headers=None, query_string=query_string, request_body=request_body,
                       module_name=module_name, function_name=function_name, function_params=request_data)

def http_handle(base_uri="/", body_data=None, cgi_module=True) -> HttpResponse:
    response = HttpResponse()
    try:
        # 首先处理 OPTIONS 请求（CORS 预检）
        method = os.environ.get('REQUEST_METHOD', '') if cgi_module else None
        if not method and hasattr(os.environ, 'get'):
            method = os.environ.get('REQUEST_METHOD', '')
        # 直接检查环境变量
        if cgi_module:
            method = os.environ.get('REQUEST_METHOD', '')
            if method == 'OPTIONS':
                logging.info("处理 OPTIONS 预检请求")
                response = HttpResponse(data="ok", status_code=200)
                response.fill_headers()
                if cgi_module:
                    response.output_cgi()
                return response
        
        request = get_request(base_uri, body_data, cgi_module)
        req_msg = f"{request.method} {request.request_uri}"
        req_msg += '' if not request.request_body else '\n' + request.request_body
        logging.debug(f"{req_msg}")
        # logging.debug(f"request: {request.__dict__}")
        module_name = request.module_name
        function_name = request.function_name
        if not module_name and not function_name:
            resource_uri = request.resource_uri
            if '..' in resource_uri:
                logging.warning(f"检测到路径遍历尝试: {request.request_uri}")
                raise HttpException(status_code=403, message=f"不允许访问资源： {request.request_uri}")
            frontend_path = os.environ.get('FRONTEND_PATH', '')
            if len(resource_uri) == 0:
                resource_uri = 'index.html'
            resource_path = Path(frontend_path).joinpath(resource_uri).absolute()
            if not resource_path.exists() or resource_path.is_dir():
                logging.warning(f"访问资源不存在: {resource_path}")
                raise HttpException(status_code=404, message=f"资源不存在： {request.request_uri}")
            response = HttpResponse(file=str(resource_path))
        else:
            function_params = request.function_params
            # logging.debug(f"request: {request.__dict__}")
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            response = func(function_params)
            if not isinstance(response, HttpResponse):
                response = HttpResponse(data=response)
    except HttpException as e:
        logging.exception(f"HTTP 异常: {e.status_code} - {e.message}")
        response = HttpResponse(code=1, status_code=e.status_code, data=e.message, headers=e.headers)
    except ImportError as e:
        logging.exception(f"模块导入失败: {str(e)}", exc_info=True)
        response = HttpResponse(code=1, status_code=500, data="模块加载失败")
    except AttributeError as e:
        if str(e).startswith("module 'actions.peers' has no attribute"):
            logging.exception(f"函数不存在: {str(e)}", exc_info=True)
            response = HttpResponse(code=1, status_code=404, data="接口不存在")
        else:
            logging.exception(e)
            response = HttpResponse(code=1, status_code=500, data=str(e))
    except Exception as e:
        logging.exception(f"服务异常: {str(e)}")
        # 生产环境不暴露详细错误信息
        safe_error_msg = str(e) or "服务器内部错误，请稍后重试"
        response = HttpResponse(code=1, status_code=500, data=safe_error_msg)
    finally:
        response.fill_headers()
        resp_msg = ''
        # resp_msg = f"Status Code: {response.status_code}"
        # resp_msg += '' if not response.headers else '\nHeaders: ' + json.dumps(response.headers)
        resp_msg += '' if not response.json else 'Response JSON: ' + json.dumps(response.json, ensure_ascii=False)
        resp_msg += '' if not response.file else 'Download File: ' + response.file
        logging.debug(f"{resp_msg}")
        if cgi_module:
            response.output_cgi()
        return response