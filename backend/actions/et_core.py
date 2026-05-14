#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import platform
import shutil
import sys
import time
import zipfile
from pathlib import Path

import utils.common_util as common_util
import utils.github_util as github_util
from actions import services
from http_dispatcher.dispatcher import HttpException
from utils import run_configs


def check_core(*kwargs):
    core_dir = run_configs.core_dir()
    ext = ".exe" if sys.platform == "win32" else ""
    cli_file = f'{core_dir}/easytier-cli{ext}'
    core_file = f'{core_dir}/easytier-core{ext}'
    return os.path.exists(cli_file) and os.path.exists(core_file)

def version(*kwargs):
    if not check_core():
        raise HttpException('内核不存在，请先安装内核')
        
    core_dir = run_configs.core_dir();
    ext = ".exe" if sys.platform == "win32" else ""
    cmd = f'{core_dir}/easytier-core{ext} --version'
    raw_version = common_util.run_cmd(cmd)
    raw_version = raw_version.replace('easytier-core ', '')
    et_version = raw_version[:raw_version.index('-')]
    return { 'version': f'v{et_version}', 'raw_version': raw_version }

def install(data, *kwargs):
    et_version = data['version']
    if not et_version:
        raise HttpException('版本不能为空')

    arch = __get_arch()
    platform = 'linux' if sys.platform == 'linux' else ('windows' if sys.platform == 'win32' else 'macos')
    url = f"https://github.com/easyTier/easytier/releases/download/{et_version}/easytier-{platform}-{arch}-{et_version}.zip"
    logging.info(f"内核下载地址: {url}")
    core_dir = run_configs.core_dir()
    zip_file = f'{core_dir}/easytier-{platform}-{arch}-{et_version}.zip'
    github_util.download_file(url, zip_file)
    unzip_temp_dir = __unzip(zip_file, f'{core_dir}')

    stop_profiles = services.stop_all()
    for item in Path(os.path.join(unzip_temp_dir, f'easytier-{platform}-{arch}')).iterdir():
        shutil.move(str(item), os.path.join(core_dir, item.name))
        logging.info(f"移动: {item.name}")
    Path(zip_file).unlink()
    shutil.rmtree(unzip_temp_dir)
    logging.info(f'安装{et_version}版本成功')
    for profile in stop_profiles:
        logging.info(f'启动配置：{profile}')
        services.start({'profile': profile})

def __get_arch():
    machine = platform.machine()
    machine = machine.lower()
    arch_map = {
        'amd64': 'x86_64',
        'x86_64': 'x86_64',
        'aarch64': 'aarch64',
        'arm64': 'aarch64',  # macOS 叫 arm64，Linux 叫 aarch64
        'i386': 'x86',
        'i686': 'x86',
        'armv7l': 'armv7',
    }
    return arch_map.get(machine, machine)

def __unzip(zip_file, unzip_dir):    
    unzip_temp_dir = f"{unzip_dir}/{int(time.time())}"
    logging.info(f"解压: {zip_file} -> {unzip_temp_dir}")
    with zipfile.ZipFile(zip_file, 'r') as zf:
        # zf.extractall(unzip_temp_dir)
        for info in zf.infolist():
            # 🔴 关键：统一转换为系统分隔符，再处理
            # zipfile 读取的 filename 可能是 / 或 \，统一用 /
            normalized_path = info.filename.replace('\\', '/')            
            # 构建本地文件系统路径（自动适应 Windows/Unix）
            local_path = os.path.join(unzip_temp_dir, *normalized_path.split('/'))            
            if info.is_dir():
                os.makedirs(local_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with zf.open(info) as src, open(local_path, 'wb') as dst:
                    dst.write(src.read())
    logging.info(f"解压完成: {zip_file} -> {unzip_temp_dir}")
    return unzip_temp_dir