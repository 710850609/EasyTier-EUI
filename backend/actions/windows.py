#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import time
import zipfile
from pathlib import Path

import actions.configs as configs
import utils.common_util as common_util
import utils.et_util as et_util
import utils.github_util as github_util
from utils import run_configs
from http_dispatcher.dispatcher import HttpResponse


def download_mgr_pro(params:dict, *kwargs):
    profile = params.get('profile', '') if params is not None else None
    download_dir = os.path.join(run_configs.data_dir(), 'download')
    download_temp_dir = f"{download_dir}/temp"
    et_version = et_util.get_latest_version()
    et_package = et_util.download_package(download_dir, 'windows', 'x86_64', et_version)
    et_mgr_version = _get_et_mgr_latest_version()
    et_mgr_package = _get_et_mgr_package(et_mgr_version, download_dir)
    output_file = f"{download_temp_dir}/easytier-manager-pro-v{et_mgr_version}-v{et_version}.zip"
    _merge_package(profile, et_package, et_mgr_package, output_file, download_temp_dir)
    return HttpResponse(file=output_file, download_name=Path(output_file).name)

def _get_et_mgr_latest_version():
    api_url = "https://api.github.com/repos/EasyTier/easytier-manager/releases/latest"
    return github_util.get_latest_version(api_url)

def _get_et_mgr_package(et_mgr_version: str, download_dir: str):
    # 不直接下载最新版本，先查版本号，方便保存文件名带版本号，用于后续自动下载最新版本
    # https://github.com/EasyTier/easytier-manager/releases/latest/download/easytier-manager-pro.zip
    last_version = et_mgr_version
    download_file = download_dir + f"/easytier-manager-pro-v{last_version}.zip"
    if Path(download_file).exists():
        logging.debug(f"已存在缓存:{download_file}")
        return download_file
    logging.debug(f"不存在缓存，开始下载 {download_file}")
    download_url = f"https://github.com/EasyTier/easytier-manager/releases/download/v{last_version}/easytier-manager-pro.zip"
    download_temp_file = f"{download_dir}/temp/easytier-manager-pro-v{last_version}.zip.{int(time.time())}"
    github_util.download_file(download_url, download_temp_file, f"easytier-windows-pro-v{last_version}.zip")
    common_util.move(download_temp_file, download_file)
    logging.debug(f"已下载： {download_file}")
    return download_file

def _merge_package(profile, et_package, et_mgr_package, output_file, unzip_dir):
    unzip_temp_dir = f"{unzip_dir}/{int(time.time())}"
    logging.info(f"解压: {et_mgr_package} -> {unzip_temp_dir}")
    with zipfile.ZipFile(et_mgr_package, 'r') as zf:
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
    logging.info(f"解压: {et_package} -> {unzip_temp_dir}")
    with zipfile.ZipFile(et_package, 'r') as zf:
        zf.extractall(unzip_temp_dir)
    logging.info(f"移动: {unzip_temp_dir}/easytier-windows-x86_64  ->  {unzip_temp_dir}/resource")
    common_util.move(f"{unzip_temp_dir}/easytier-windows-x86_64", f"{unzip_temp_dir}/resource")
    # shutil.rmtree(f"{unzip_temp_dir}/easytier-windows-x86_64")
    if profile:
        logging.info(f"内置配置文件：{profile}")
        config_file = configs.copy(profile)
        cfg_target_file = f"{unzip_temp_dir}/config/{profile}"
        Path(cfg_target_file).parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"复制: {config_file}  ->  {cfg_target_file}")
        common_util.move(f"{config_file}", f"{cfg_target_file}")
    else:
        logging.info(f"未指定profile，不内置配置文件")

    logging.info(f"开始打包: {output_file}")
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in Path(unzip_temp_dir).rglob('*'):
            if item.is_file():
                arch_name = item.relative_to(unzip_temp_dir)
                zf.write(item, arch_name)
    common_util.delete(unzip_temp_dir)