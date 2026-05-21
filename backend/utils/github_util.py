#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import re
from pathlib import Path
from utils import run_configs

import requests


def get_latest_version(api_url) -> str:
    """
    获取最新版本，如：https://api.github.com/repos/EasyTier/easytier-manager/releases/latest
    合适 提取版本号 v1.2.3 -> 1.2.3
    """
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        tag_name = data.get('tag_name', '')
        # 提取版本号 v1.2.3 -> 1.2.3
        match = re.search(r'(\d+\.\d+\.\d+)', tag_name)
        if match:
            return match.group(1)
        raise ValueError(f"无法解析版本号: {tag_name}")
    except Exception as e:
        logging.error(f"获取 manager 版本失败: {e}")
        raise

def get_github_proxy() -> str:
    """获取 GitHub 代理 URL"""
    try:
        github_proxy_file = run_configs.github_proxy_file()
        if not Path(github_proxy_file).exists():
            logging.warning(f"GitHub加速配置文件不存在: {github_proxy_file}，不使用加速")
            return None
        cfg_path = Path(github_proxy_file)
        if cfg_path.exists():
            content = cfg_path.read_text().strip()
            # 去除空行
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            return lines[0] if lines else ""
    except Exception as e:
        logging.warning(f"读取代理配置失败: {e}")
    return ""

def get_download_url_proxy(url: str) -> str:
    """获取 GitHub 代理 URL"""
    proxy_url = get_github_proxy()
    if proxy_url and proxy_url != '':
        logging.info(f"使用加速地址: {proxy_url}")
        url = proxy_url + '/' + url
    return url

def download_file(url: str, output_path: str, desc: str = ""):
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
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logging.debug(f"{desc} xia'z进度: {percent:.1f}%")
        
        logging.info(f"下载成功: {output_path}")        
    except Exception as e:
        logging.exception(f"下载失败")
        if output_path.exists():
            output_path.unlink()
        raise Exception(f"下载失败：{e}") from e
    
