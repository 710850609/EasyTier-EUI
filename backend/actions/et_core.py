#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import platform
import shutil
import sys
import time
import zipfile
from pathlib import Path
import requests
import utils.github_util as github_util
from actions import services
from et_adapters import get_facade
from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import run_configs, et_run_info
from utils.validators import Validator

logger = logging.getLogger(__name__)

def get_log_level(params:dict, *args, **kwargs):
    log_level = et_run_info.get_log_level()
    return log_level

def set_log_level(params:dict, *args, **kwargs):
    params = params or {}
    log_level = params.get("level", 'error')
    et_run_info.set_log_level(log_level)
    services.change_log_level(log_level)

def version(params=None, *args, **kwargs):
    ver = get_facade().get_version()
    dash_idx = ver.find('-')
    et_version = ver[:dash_idx] if dash_idx > 0 else ver
    return {'version': f'v{et_version}', 'raw_version': f'easytier-core {ver}'}

def get_release_info(params: dict, *args, **kwargs) -> dict:
    params = params or {}
    refresh = params.get('refresh', 'false').lower() == 'true'
    release_file = Path(run_configs.data_dir()).joinpath('et_release.json')
    release_info = None
    if os.path.exists(release_file):
        with open(release_file, "r", encoding="utf-8") as f:
            release_info = json.load(f)

    cur_time = int(time.time() * 1000)
    cur_diff_time = cur_time - (release_info or {}).get('update_time', 0)
    cache_time = 1000 * 60
    if refresh or release_info is None:
        if cur_diff_time < cache_time and release_info is not None:
            logger.info(f'上次刷新时间距离当前时间仅隔 {cur_diff_time} ms, 直接返回上次刷新结果')
            return release_info or {}
        total_download = 0
        versions = []
        release_info = {'update_time': cur_time, 'total_download': total_download, 'versions': versions}
        releases = github_util.get_api('https://api.github.com/repos/EasyTier/EasyTier/releases?per_page=100')
        for item in releases:
            item_download_count = 0
            assets = {}
            ver = item.get('name')
            info = {'version': ver, 'prerelease': item['prerelease'], 'download_count': item_download_count, 'assets': assets, 'changelog': item.get('body')}
            versions.append(info)
            for asset in item['assets']:
                download_count = asset.get('download_count', 0)
                item_download_count += download_count
                total_download += download_count
                filename = asset.get('name')
                need_platform = ['linux', 'windows', 'macos']
                need_arch = ['x86_64', 'aarch64', 'armv7', 'riscv64']
                if filename.startswith('easytier-') and filename.endswith(f'{ver}.zip'):
                    # 只取核心包 只适配部分平台架构
                    platform_arch = filename.replace('easytier-', '').replace(f'-{ver}.zip', '')
                    t_p_a = platform_arch.split('-')
                    if t_p_a[0] in need_platform and t_p_a[1] in need_arch:
                        assets[platform_arch] = {'download_url': asset.get('browser_download_url', ''), 'download_count': download_count}
                elif filename.startswith('app-') and filename.endswith('-release.apk'):
                    # 只取安卓应用包
                    platform_arch = filename.replace('app-', '').replace('release.', '')
                    assets[platform_arch] = {'download_url': asset.get('browser_download_url', ''), 'download_count': download_count}
                elif filename.startswith('easytier-gui') :
                    # 只取gui包
                    rel_ver = ver.replace('v', '')
                    platform_arch = filename.replace(f'easytier-gui_{rel_ver}_', '')
                    platform_arch = platform_arch.replace(f'easytier-gui-{rel_ver}-1.', '') # 针对rpm包 特殊处理 easytier-gui-2.6.4-1.x86_64.rpm
                    platform_arch = platform_arch.replace(f'-setup', '') # 针对exe包 特殊处理 easytier-gui_2.6.4_x86-setup.exe
                    platform_arch = platform_arch.replace('.', '-')
                    assets[platform_arch] = {'download_url': asset.get('browser_download_url', ''), 'download_count': download_count}

            info['download_count'] = item_download_count
        release_info['total_download'] = total_download
        with open(release_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(release_info, ensure_ascii=False, indent=2))
    return release_info

def version_list(params: dict, *args, **kwargs):
    release_info = get_release_info(params)
    # 减少返回数据量
    for ver in release_info.get('versions', []):
        ver.pop('assets', None)
        ver.pop('changelog', None)
    return release_info

def version_changelog(params: dict, *args, **kwargs):
    params = params or {}
    select_ver, _ = Validator.not_empty(params, 'version', 'validate.version_required')
    release_info = get_release_info({})
    changelog = ''
    for ver in release_info.get('versions', []):
        if ver.get('version') == select_ver:
            changelog = ver.get('changelog')
            break
    return changelog

def install(data, *args, **kwargs):
    if run_configs.IS_ANDROID:
        ffi_version = data.get('version', '')
        if not ffi_version:
            raise HttpException(get_message('download.id_required', param='version'))
        ffi_url = data.get('url', 'http://192.168.220.12:18080/')
        if not ffi_url:
            raise HttpException(get_message('download.id_required', param='url'))
        # ffi_arch = __get_arch()
        ffi_filename = 'libeasytier_ffi.so'

        ffi_dir = os.path.join(os.environ['ANDROID_DATA_DIR'], 'libs')
        os.makedirs(ffi_dir, exist_ok=True)
        ffi_path = os.path.join(ffi_dir, ffi_filename)
        tmp_path = ffi_path + '.tmp'
        logger.info(f"FFI 下载地址: {ffi_url}")
        logger.info(f"FFI 保存路径: {ffi_path}")
        resp = requests.get(ffi_url, stream=True, timeout=300)
        resp.raise_for_status()
        with open(tmp_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        if os.path.getsize(tmp_path) == 0:
            os.remove(tmp_path)
            raise HttpException(get_message('download.download_failed'))
        if os.path.exists(ffi_path):
            os.remove(ffi_path)
        os.rename(tmp_path, ffi_path)
        os.chmod(ffi_path, 0o555)
        logger.info(f'FFI {ffi_version} 安装成功，重启后生效')
        return {'success': True, 'message': 'ffi_installed', 'ffi_version': ffi_version}

    et_version = data['version']
    if not et_version:
        raise HttpException(get_message('download.id_required', param='version'))
    arch = __get_arch()
    platform = 'linux' if sys.platform == 'linux' else ('windows' if sys.platform == 'win32' else 'macos')
    url = f"https://github.com/easyTier/easytier/releases/download/{et_version}/easytier-{platform}-{arch}-{et_version}.zip"
    logger.info(f"内核下载地址: {url}")
    core_dir = run_configs.core_dir()
    run_configs.data_dir()
    output_dir = os.path.join(run_configs.data_dir(), 'download')
    zip_file = f'{output_dir}/easytier-{platform}-{arch}-{et_version}.zip'
    github_util.download_release_file(url, zip_file)
    unzip_temp_dir = __unzip(zip_file, os.path.join(run_configs.data_dir(), 'download', 'temp'))

    stop_profiles = services.stop_all()
    for item in Path(os.path.join(unzip_temp_dir, f'easytier-{platform}-{arch}')).iterdir():
        dst = os.path.join(core_dir, item.name)
        shutil.move(str(item), dst)
        if sys.platform != 'win32':
            # unzip 出来是 rw-r--r-- ，需要添加执行权限
            import stat
            os.chmod(dst, os.stat(dst).st_mode | stat.S_IEXEC)
        logger.info(f"移动: {item.name}")
    Path(zip_file).unlink()
    shutil.rmtree(unzip_temp_dir)
    logger.info(f'安装{et_version}版本成功')
    for profile in stop_profiles:
        logger.info(f'启动配置：{profile}')
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
    logger.info(f"解压: {zip_file} -> {unzip_temp_dir}")
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
    logger.info(f"解压完成: {zip_file} -> {unzip_temp_dir}")
    return unzip_temp_dir

if __name__ == '__main__':
    run_configs.setup_env()
    # log_util.setup_log(log_level="DEBUG")
    # get_release_info({'refresh': 'true'})
    # print(version_list({}))