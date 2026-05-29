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


def download_easytier_eui(params:dict, *kwargs):
    if not params:
        raise HttpResponse(f"未指定platfrom和arch参数")
    download_dir = os.path.join(run_configs.data_dir(), 'download')
    et_lite_version = _get_et_eui_latest_version()
    platform = params.get('platform', '')
    arch = params.get('arch', '')
    profile = params.get('profile', '')
    et_lite_package = _get_et_eui_package(platform, arch, et_lite_version, download_dir)
    if platform == 'fnos':
        return HttpResponse(file=et_lite_package, download_name=os.path.basename(et_lite_package))
    else:
        et_lite_filename = Path(et_lite_package).name
        output_file = f"{download_dir}/temp/{et_lite_filename.replace('.zip', '_merge.zip')}"
        _merge_package(profile, et_lite_package, output_file, download_dir)
        return HttpResponse(file=output_file, download_name=et_lite_filename)

def _get_et_eui_latest_version():
    api_url = "https://api.github.com/repos/710850609/EasyTier-EUI/releases/latest"
    return github_util.get_latest_version(api_url)

def _get_et_eui_package(platform:str, arch:str, et_lite_version: str, download_dir: str):
    support_platforms = ['windows', 'linux', 'macos', 'fnos']
    if platform not in support_platforms:
        raise HttpResponse(f"当前不支持 {platform} 平台下载，仅支持 {support_platforms}")
    support_arches = ['x86_64', 'aarch64', 'riscv64']
    if arch not in support_arches:
        raise HttpResponse(f"当前不支持 {arch} 架构下载，仅支持 {support_arches}")

    last_version = et_lite_version
    file_name = f"EasyTier-EUI-{platform}-{arch}-{last_version}.zip"
    if platform == 'fnos':
        file_name = file_name.replace('.zip', '.fpk')
    download_file = download_dir + '/' + file_name
    if Path(download_file).exists():
        logging.debug(f"已存在缓存:{download_file}")
        return download_file
    download_url = f"https://github.com/710850609/EasyTier-EUI/releases/download/{last_version}/{file_name}"
    logging.debug(f"不存在缓存，开始下载 {download_url}")
    download_temp_file = f"{download_dir}/temp/{file_name}.{int(time.time())}"
    github_util.download_file(download_url, download_temp_file, Path(download_temp_file).name)
    common_util.move(download_temp_file, download_file)
    logging.debug(f"已下载： {download_file}")
    return download_file

    
def _merge_package(profile, et_lite_package, output_file, unzip_dir):
    unzip_temp_dir = f"{unzip_dir}/temp/{int(time.time())}"
    logging.info(f"解压: {et_lite_package} -> {unzip_temp_dir}")
    config_path = ''
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
                if local_path == 'core':
                    config_path = os.path.dirname(local_path) + '/config'
            else:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with zf.open(info) as src, open(local_path, 'wb') as dst:
                    dst.write(src.read())
    if profile:
        logging.info(f"内置配置文件：{profile}")
        config_file = configs.copy(profile)
        cfg_target_file = f"{config_path}/{profile}"
        Path(cfg_target_file).parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"复制: {config_file}  ->  {cfg_target_file}")
        common_util.move(f"{config_file}", f"{cfg_target_file}")
    else:
        logging.info(f"未指定profile，不内置配置文件")
    

    logging.info(f"开始打包: {output_file}")
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in Path(unzip_temp_dir).rglob('*'):
            if item.is_file():
                arch_name = item.relative_to(unzip_temp_dir)
                zf.write(item, arch_name)
    common_util.delete(unzip_temp_dir)