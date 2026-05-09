#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import time
import zipfile
from pathlib import Path

import actions.configs as configs
import utils.common_util as common_util
import utils.github_util as github_util
from http_dispatcher.dispatcher import HttpResponse
from utils import run_configs


def download_easytier_lite(params:dict, *kwargs):
    if not params:
        raise HttpResponse(f"未指定platfrom和arch参数")
    output_dir = run_configs.data_dir()
    download_temp_dir = f"{output_dir}/tmp"
    et_lite_version = _get_et_lite_latest_version()
    platform = params.get('platform', '')
    arch = params.get('arch', '')
    et_lite_package = _get_et_lite_package(platform, arch, et_lite_version, download_temp_dir)
    et_lite_filename = Path(et_lite_package).name
    output_file = f"{output_dir}/{et_lite_filename.replace('.zip', '_merge.zip')}"
    _merge_et_lite_package(et_lite_package, output_file, download_temp_dir)
    return HttpResponse(file=output_file, download_name=et_lite_filename)

def _get_et_lite_latest_version():
    api_url = "https://api.github.com/repos/710850609/EasyTier-Lite/releases/latest"
    return github_util.get_latest_version(api_url)

def _get_et_lite_package(platform:str, arch:str, et_lite_version: str, download_dir: str):
    support_platforms = ['windows', 'linux', 'macos', 'fnos']
    if platform not in support_platforms:
        raise HttpResponse(f"当前不支持 {platform} 平台下载，仅支持 {support_platforms}")
    support_arches = ['x86_64', 'aarch64', 'riscv64']
    if arch not in support_arches:
        raise HttpResponse(f"当前不支持 {arch} 架构下载，仅支持 {support_arches}")

    last_version = et_lite_version
    download_file = download_dir + f"/easytier-lite-{platform}-{arch}-{last_version}.zip"
    if Path(download_file).exists():
        logging.debug(f"已存在缓存:{download_file}")
        return download_file
    logging.debug(f"不存在缓存，开始下载 {download_file}")
    download_url = f"https://github.com/710850609/EasyTier-Lite/releases/download/{last_version}/easytier-lite-{platform}-{arch}-{last_version}.zip"
    github_proxy = github_util.get_github_proxy()
    if github_proxy and github_proxy != '':
        download_url = f"{github_proxy}/{download_url}"
    download_temp_file = f"{download_dir}/easytier-lite-{platform}-{arch}-{last_version}.zip.{int(time.time())}"
    github_util.download_file(download_url, download_temp_file, Path(download_temp_file).name)
    common_util.move(download_temp_file, download_file)
    logging.debug(f"已下载： {download_file}")
    return download_file

    
def _merge_et_lite_package(et_lite_package, output_file, unzip_dir):
    unzip_temp_dir = f"{unzip_dir}/{int(time.time())}"
    logging.info(f"解压: {et_lite_package} -> {unzip_temp_dir}")
    with zipfile.ZipFile(et_lite_package, 'r') as zf:
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
    config_file = configs.copy()
    cfg_target_file = f"{unzip_temp_dir}/config/default.toml"
    Path(cfg_target_file).parent.mkdir(parents=True, exist_ok=True)
    logging.info(f"复制: {config_file}  ->  {cfg_target_file}")
    common_util.move(f"{config_file}", f"{cfg_target_file}")
    

    logging.info(f"开始打包: {output_file}")
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in Path(unzip_temp_dir).rglob('*'):
            if item.is_file():
                arch_name = item.relative_to(unzip_temp_dir)
                zf.write(item, arch_name)
    common_util.delete(unzip_temp_dir)