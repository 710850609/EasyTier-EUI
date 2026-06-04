#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import gzip
import json
import logging
import os
import shutil
import sys
import platform
import tarfile
import time
import zipfile
from pathlib import Path

import psutil

import actions.configs as configs
import utils.common_util as common_util
import utils.github_util as github_util
from actions import services
from http_dispatcher.dispatcher import HttpResponse
from utils import run_configs

def update(params: dict, *kwargs):
    params = params or {}
    ver_tag = params.get('ver_tag', '')
    if ver_tag not in ('release', 'prerelease'):
        raise HttpResponse(f"版本标签错误：{ver_tag}")
    download_url, filename = __get_download_url(ver_tag == 'release')
    download_dir = os.path.join(run_configs.data_dir(), 'download')
    download_file = os.path.join(download_dir, filename)
    if not os.path.exists(download_file):
        github_util.download_release_file(download_url, download_file)
    extract_dir = os.path.join(download_dir, 'temp', str(int(time.time())))
    if run_configs.is_fn_system():
        # fpk是gzip压缩的文件
        os.makedirs(extract_dir, exist_ok=True)
        with tarfile.open(download_file, 'r:gz') as tar:
            tar.extractall(path=extract_dir)
            # 可选：列出解压的内容
            for member in tar.getmembers():
                print(member.name)
        app_dir = os.path.join(extract_dir, 'app')
        with tarfile.open(os.path.join(extract_dir, 'app.tgz'), 'r:gz') as tar:
            tar.extractall(path=app_dir)
        backend_path = Path(run_configs.core_dir()).parent.joinpath('backend')
        shutil.copytree(os.path.join(app_dir, 'backend'), backend_path, dirs_exist_ok=True)
        logging.info(f"更新backend： {backend_path}")
        frontend_path = Path(run_configs.core_dir()).parent.joinpath('frontend')
        shutil.copytree(os.path.join(app_dir, 'frontend'), frontend_path, dirs_exist_ok=True)
        logging.info(f"更新frontend： {frontend_path}")
        pass
    else:
        services.stop_all()
        _extract_package(download_file, extract_dir)
        app_path = Path(run_configs.core_dir()).parent
        shutil.copytree(os.path.join(extract_dir, 'EasyTier-EUI'), app_path.joinpath('_update'), dirs_exist_ok=True)
        upgrade_script = run_configs.upgrade_script_path()
        cmd = [upgrade_script, str(app_path)]
        logging.info(f"执行升级脚本：{' '.join(cmd)}")
        common_util.run_cmd(cmd)
    pass



def version_list(params: dict, *kwargs):
    refresh = params.get('refresh', False)
    version_file = Path(run_configs.data_dir()).joinpath('et_versions.json')
    release_info = {'create_time': time.time(), 'versions': []}
    if not version_file.exists() or refresh:
        releases = github_util.get_api('https://api.github.com/repos/10850609/EasyTier-EUI/releases')
        for item in releases:
            release_info['versions'].append({'version': item.get('name'), 'prerelease': item.get('prerelease')})
        with open(version_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(release_info, ensure_ascii=False, indent=2))
    else:
        with open(version_file, "r", encoding="utf-8") as f:
            release_info = json.load(f)
    return release_info

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
    github_util.download_release_file(download_url, download_temp_file, Path(download_temp_file).name)
    common_util.move(download_temp_file, download_file)
    logging.debug(f"已下载： {download_file}")
    return download_file

    
def _merge_package(profile, et_lite_package, output_file, unzip_dir):
    unzip_temp_dir = f"{unzip_dir}/temp/{int(time.time())}"
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
    if profile:
        logging.info(f"内置配置文件：{profile}")
        config_file = configs.copy(profile)
        cfg_target_file = Path(unzip_temp_dir, 'EasyTier-EUI', 'config', profile)
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

def _extract_package(package_file:str, extract_dir:str):
    logging.info(f"解压: {package_file} -> {extract_dir}")
    with zipfile.ZipFile(package_file, 'r') as zf:
        # zf.extractall(unzip_temp_dir)
        for info in zf.infolist():
            # 🔴 关键：统一转换为系统分隔符，再处理
            # zipfile 读取的 filename 可能是 / 或 \，统一用 /
            normalized_path = info.filename.replace('\\', '/')
            # 构建本地文件系统路径（自动适应 Windows/Unix）
            local_path = os.path.join(extract_dir, *normalized_path.split('/'))
            if info.is_dir():
                os.makedirs(local_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with zf.open(info) as src, open(local_path, 'wb') as dst:
                    dst.write(src.read())

def __get_download_url(is_release: bool) -> tuple[str, str]:
    # 系统映射
    sys_map = {
        "win32": "windows",
        "linux": "linux",
        "darwin": "macos"
    }
    # 架构映射
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "riscv64": "riscv64",
        "armv7l": "armv7"
    }
    system = sys.platform
    machine = os.uname().machine if hasattr(os, 'uname') else platform.machine()
    sys_name = sys_map.get(system, system)
    arch_name = arch_map.get(machine.lower())
    if run_configs.is_fn_system():
        sys_name = 'fnos'
    release_infos = github_util.get_api("https://api.github.com/repos/710850609/EasyTier-EUI/releases")
    release_info = {}
    for item in release_infos:
        prerelease = item.get('prerelease', '')
        if prerelease and not is_release:
            release_info = item
            break
        if not prerelease and is_release:
            release_info = item
            break
    if not release_info or not release_info.get('assets', []):
        raise HttpResponse(f"没有可下载版本")

    assets = release_info.get('assets', [])
    package_prefix = f"EasyTier-EUI-{sys_name}-{arch_name}"
    download_url = ''
    filename = ''
    for asset in assets:
        if asset.get('name', '').startswith(package_prefix):
            download_url = asset.get('browser_download_url', '')
            filename = asset.get('name', '')
            break
    if not download_url:
        raise HttpResponse(f"没有可下载版本")
    return download_url, filename

if __name__ == '__main__':
    run_configs.setup_env()
    update({'ver_tag': 'release'})