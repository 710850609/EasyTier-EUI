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
from locales import get_message
from utils.async_task import DownloadTask
from http_dispatcher.dispatcher import HttpResponse
from utils import run_configs


def download_mgr_pro(params:dict, *args, **kwargs):
    profile = params.get('profile', '') if params is not None else None
    task = DownloadTask(params)
    task.update_progress(0, get_message('download.init_task'))
    task.start(_do_download_mgr_pro, profile)
    return HttpResponse(data={'download_id': task.download_id})


def get_download_mgr_pro_progress(params:dict, *args, **kwargs):
    download_id = params.get('download_id', '')
    if not download_id:
        raise HttpResponse(get_message('download.id_required', param='download_id'))
    progress = DownloadTask.load(download_id)
    if progress is None:
        raise HttpResponse(get_message('download.task_not_found', id=download_id))
    progress.pop('file_path', None)
    progress.pop('file_name', None)
    return HttpResponse(data=progress)


def download_mgr_pro_result(params:dict, *args, **kwargs):
    download_id = params.get('download_id', '')
    if not download_id:
        raise HttpResponse(get_message('download.id_required', param='download_id'))
    progress = DownloadTask.load(download_id)
    if progress is None:
        raise HttpResponse(get_message('download.task_not_found', id=download_id))
    status = progress.get('status')
    if status == 0:
        raise HttpResponse(get_message('download.not_completed'))
    if status == 2:
        raise HttpResponse(get_message('download.failed', error=progress.get('description')))
    file_path = progress.get('file_path')
    file_name = progress.get('file_name')
    if not file_path or not os.path.exists(file_path):
        raise HttpResponse(get_message('download.file_not_found'))
    return HttpResponse(file=file_path, download_name=file_name)


def _do_download_mgr_pro(task: DownloadTask, profile: str):
    download_dir = os.path.join(run_configs.data_dir(), 'download')
    task.update_progress(5, get_message('download.fetching_version'))
    et_version = et_util.get_latest_version()
    task.update_progress(10, get_message('download.preparing') + f' ({et_version})')

    def on_et_download(percent, desc):
        mapped = 10 + int(percent * 0.40)
        task.update_progress(mapped, get_message('download.downloading_core') + f' {et_version}({desc or percent})')

    et_package = et_util.download_package(download_dir, 'windows', 'x86_64', et_version, progress_callback=on_et_download)
    task.update_progress(50, get_message('download.fetching_version') + ' - EasyTier Manager')
    et_mgr_version = _get_et_mgr_latest_version()
    task.update_progress(55, get_message('download.preparing') + f' ({et_mgr_version})')

    def on_mgr_download(percent, desc):
        mapped = 55 + int(percent * 0.35)
        task.update_progress(mapped, get_message('download.downloading_manager') + f' {et_mgr_version}({desc or percent})')

    et_mgr_package = _get_et_mgr_package(et_mgr_version, download_dir, progress_callback=on_mgr_download)
    task.update_progress(90, get_message('download.merging_package'))
    download_temp_dir = f"{download_dir}/temp"
    output_file = f"{download_temp_dir}/easytier-manager-pro-v{et_mgr_version}-v{et_version}.zip"
    _merge_package(profile, et_package, et_mgr_package, output_file, download_temp_dir)
    task.update_progress(95, get_message('download.preparing'))
    task.set_completed(output_file, Path(output_file).name)


def _get_et_mgr_latest_version():
    api_url = "https://api.github.com/repos/EasyTier/easytier-manager/releases/latest"
    return github_util.get_latest_version(api_url)

def _get_et_mgr_package(et_mgr_version: str, download_dir: str, progress_callback=None):
    # 不直接下载最新版本，先查版本号，方便保存文件名带版本号，用于后续自动下载最新版本
    # https://github.com/EasyTier/easytier-manager/releases/latest/download/easytier-manager-pro.zip
    last_version = et_mgr_version
    download_file = download_dir + f"/easytier-manager-pro-v{last_version}.zip"
    if Path(download_file).exists():
        logging.debug(f"已存在缓存:{download_file}")
        return download_file
    logging.debug(f"不存在缓存，开始下载 {download_file}")
    download_url = f"https://github.com/EasyTier/easytier-manager/releases/download/v{last_version}/easytier-manager-pro.zip"
    github_util.download_release_file(download_url, download_file, f"easytier-windows-pro-v{last_version}.zip", progress_callback=progress_callback)
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