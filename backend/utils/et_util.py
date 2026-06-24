#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
from pathlib import Path

import utils.common_util as common_util
import utils.github_util as github_util

et_min_version = "2.5.0"

def get_package_name(system:str, arch: str, version: str=None):
    if system == 'android':
        return 'app-universal-release.apk'
    elif system == 'windows' or arch == 'linux' or arch == 'macos':
        if version is None:
            version = get_latest_version()
        return f'easytier-{system}-{arch}-v{version}.zip';
    else:
        raise ValueError(f"不支持的系统或架构: {system}/{arch}")

def get_latest_version():
    api_url = "https://api.github.com/repos/EasyTier/EasyTier/releases/latest"
    last_version = github_util.get_latest_version(api_url)
    if last_version < et_min_version:
        logging.debug(f"最新release小于 {et_min_version}, 使用 {et_min_version}")
        last_version = et_min_version
    return last_version

def get_download_url(system:str, arch: str, version: str=None):
    if version is None:
        version = get_latest_version()
    url = f"https://github.com/EasyTier/EasyTier/releases/download/v{version}/{get_package_name(system, arch, version)}"
    return github_util.get_download_url_proxy(url)

def download_package(download_dir: str, system: str, arch: str, version: str=None, progress_callback=None):
    if  version is None or version == '':
        version = get_latest_version()
    download_file_name = get_package_name(system, arch, version)
    logging.debug(f"下载 {system}/{arch} 版本 {version} 包 {download_file_name}")
    download_file = download_dir + '/' + download_file_name
    if Path(download_file).exists():
        logging.debug(f"已存在缓存:{download_file}")
        return download_file;
    logging.debug(f"不存在缓存，开始下载 {download_file}")
    download_url = f"https://github.com/EasyTier/EasyTier/releases/download/v{version}/{download_file_name}"
    github_util.download_release_file(download_url, download_file, download_file_name, progress_callback=progress_callback)
    logging.debug(f"已下载： {download_file}")
    return download_file