#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import platform
import shutil
import sys
import tarfile
import time
import zipfile
from pathlib import Path

import utils.download_manager as download_manager
from utils.download_manager import DownloadTask
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
        app_dir = os.path.join(extract_dir, 'app')
        with tarfile.open(os.path.join(extract_dir, 'app.tgz'), 'r:gz') as tar:
            tar.extractall(path=app_dir)
        backend_path = Path(run_configs.core_dir()).parent.joinpath('backend')
        shutil.copytree(os.path.join(app_dir, 'backend'), backend_path, dirs_exist_ok=True)
        logging.info(f"更新backend： {backend_path}")
        frontend_path = Path(run_configs.core_dir()).parent.joinpath('frontend')
        shutil.copytree(os.path.join(app_dir, 'frontend'), frontend_path, dirs_exist_ok=True)
        logging.info(f"更新frontend： {frontend_path}")
        cmd = f"{backend_path}/.venv/bin/pip install --no-index --find-links={backend_path}/wheels -r {backend_path}/requirements-base.txt"
        common_util.run_cmd(cmd)
        logging.info(f"安装依赖完成")
        logging.info(f"更新到 {ver_tag} 版本完成")
        pass
    else:
        services.stop_all()
        _extract_package(download_file, extract_dir)
        app_path = Path(run_configs.core_dir()).parent
        shutil.copytree(os.path.join(extract_dir, 'EasyTier-EUI'), app_path.joinpath('_update'), dirs_exist_ok=True)
        upgrade_script = run_configs.upgrade_script_path()
        # 复制升级脚本到安装目录，避免 PyInstaller 清理 temp 目录时脚本被删除
        script_name = os.path.basename(upgrade_script)
        persistent_script = os.path.join(str(app_path), script_name)
        shutil.copy2(upgrade_script, persistent_script)
        if sys.platform != 'win32':
            # PyInstaller --add-data 不保留执行权限，用 bash 执行避免依赖 +x
            cmd = ['bash', persistent_script, str(app_path)]
        else:
            cmd = [persistent_script, str(app_path)]
        logging.info(f"执行升级脚本：{' '.join(cmd)}")
        import subprocess as _sp
        import time as _time
        if sys.platform != 'win32':
            _sp.Popen(cmd, start_new_session=True,
                      stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        else:
            _sp.Popen(cmd, stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                      cwd=str(app_path))
        logging.info("升级脚本已脱离当前进程启动，即将退出当前进程")
        # 给升级脚本一点时间启动，然后优雅退出
        _time.sleep(0.5)
        logging.shutdown()
        os._exit(0)
    pass

def get_release_info(params: dict, *kwargs):
    params = params or {}
    refresh = params.get('refresh', 'false').lower() == 'true'
    release_file = Path(run_configs.data_dir()).joinpath('eui_release.json')
    release_info = None
    if os.path.exists(release_file):
        with open(release_file, "r", encoding="utf-8") as f:
            release_info = json.load(f)

    cur_time = int(time.time() * 1000)
    cur_diff_time = cur_time - (release_info or {}).get('update_time', 0)
    cache_time = 1000 * 60
    if refresh or release_info is None:
        if cur_diff_time < cache_time and release_info is not None:
            logging.info(f'上次刷新时间距离当前时间仅隔 {cur_diff_time} ms, 直接返回上次刷新结果')
            return release_info
        total_download = 0
        release_info = {'update_time': cur_time, 'total_download': total_download, 'latest_release': {}, 'latest_prerelease': {}}
        releases = github_util.get_api('https://api.github.com/repos/710850609/EasyTier-EUI/releases?per_page=100')
        for item in releases:
            item_download_count = 0
            assets = {}
            ver = item.get('name')
            is_latest_prerelease = item['prerelease'] and not release_info['latest_prerelease']
            is_prerelease = not item['prerelease'] and not release_info['latest_release']
            for asset in item['assets']:
                download_count = asset.get('download_count', 0)
                item_download_count += download_count
                total_download += download_count
                if is_latest_prerelease or is_prerelease:
                    filename = asset.get('name')
                    download_url = asset.get('browser_download_url')
                    platform_arch = filename.replace('EasyTier-EUI-', '').replace(f'-{ver}', '').replace('.zip', '').replace('.fpk', '')
                    assets[platform_arch] = {'download_url': download_url, 'download_count': download_count}
                    info = {'version': ver, 'download_count': item_download_count, 'assets': assets, 'changelog': item.get('body')}
                    if is_latest_prerelease:
                        release_info['latest_prerelease'] = info
                    elif is_prerelease:
                        release_info['latest_release'] = info
            release_info['total_download'] = total_download
        with open(release_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(release_info, ensure_ascii=False, indent=2))
    return release_info

def download_easytier_eui(params: dict, *kwargs):
    if not params:
        raise HttpResponse(f"未指定platform和arch参数")
    platform = params.get('platform', '')
    arch = params.get('arch', '')
    profile = params.get('profile', '')
    if not platform or not arch:
        raise HttpResponse(f"platform和arch参数不能为空")

    download_id = download_manager.new_download_id()
    task = DownloadTask(download_id, params)
    task.update_progress(0, '正在初始化下载任务...')
    download_manager.run_async_download(_do_download_easytier_eui, task, platform, arch, profile)
    return HttpResponse(data={'download_id': download_id})


def get_download_progress(params: dict, *kwargs):
    download_id = params.get('download_id', '')
    if not download_id:
        raise HttpResponse(f"download_id参数不能为空")
    progress = DownloadTask.load(download_id)
    if progress is None:
        raise HttpResponse(f"下载任务不存在: {download_id}")
    progress.pop('file_path', None)
    progress.pop('file_name', None)
    return HttpResponse(data=progress)


def download_result(params: dict, *kwargs):
    download_id = params.get('download_id', '')
    if not download_id:
        raise HttpResponse(f"download_id参数不能为空")
    progress = DownloadTask.load(download_id)
    if progress is None:
        raise HttpResponse(f"下载任务不存在: {download_id}")
    status = progress.get('status')
    if status == 0:
        raise HttpResponse(f"下载尚未完成")
    if status == 2:
        raise HttpResponse(f"下载失败: {progress.get('description')}")
    file_path = progress.get('file_path')
    file_name = progress.get('file_name')
    if not file_path or not os.path.exists(file_path):
        raise HttpResponse(f"下载文件不存在")
    return HttpResponse(file=file_path, download_name=file_name)


def _do_download_easytier_eui(task: DownloadTask, platform: str, arch: str, profile: str):
    download_dir = os.path.join(run_configs.data_dir(), 'download')
    task.update_progress(5, '正在获取下载链接...')
    release_info = get_release_info({'refresh': 'false'})
    latest_release = release_info.get('latest_release', {})
    et_lite_version = latest_release.get('version', '')
    platform_arch_key = f'{platform}-{arch}'
    download_url = latest_release.get('assets', {}).get(platform_arch_key, {}).get('download_url', '')
    if not et_lite_version or not download_url:
        raise HttpResponse(f"未找到 {platform_arch_key} 的下载链接")
    task.update_progress(10, f'获取到版本: {et_lite_version}，准备下载...')

    def on_download_progress(percent, desc):
        mapped = 10 + int(percent * 0.80)
        task.update_progress(mapped, f'正在下载 EasyTier-EUI {et_lite_version}... ({percent}%)')

    et_lite_package = _get_et_eui_package_async(platform, arch, et_lite_version, download_dir, download_url=download_url, progress_callback=on_download_progress)

    if platform == 'fnos':
        task.update_progress(95, '下载完成，准备返回文件...')
        task.set_completed(et_lite_package, os.path.basename(et_lite_package))
    else:
        task.update_progress(90, '正在合并配置文件...')
        et_lite_filename = Path(et_lite_package).name
        output_file = f"{download_dir}/temp/{et_lite_filename.replace('.zip', '_merge.zip')}"
        _merge_package(profile, et_lite_package, output_file, download_dir)
        task.update_progress(95, '合并完成，准备返回文件...')
        task.set_completed(output_file, et_lite_filename)


def _get_et_eui_package_async(platform: str, arch: str, et_lite_version: str, download_dir: str, download_url: str = None, progress_callback=None):
    support_platforms = ['windows', 'linux', 'macos', 'fnos']
    if platform not in support_platforms:
        raise HttpResponse(f"当前不支持 {platform} 平台下载，仅支持 {support_platforms}")
    support_arches = ['x86_64', 'aarch64', 'riscv64', 'armv71']
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
    if not download_url:
        download_url = f"https://github.com/710850609/EasyTier-EUI/releases/download/{last_version}/{file_name}"
    logging.debug(f"不存在缓存，开始下载 {download_url}")
    download_temp_file = f"{download_dir}/temp/{file_name}.{int(time.time())}"
    github_util.download_release_file(download_url, download_temp_file, Path(download_temp_file).name, progress_callback=progress_callback)
    common_util.move(download_temp_file, download_file)
    logging.debug(f"已下载： {download_file}")
    return download_file

def _get_et_eui_latest_version():
    api_url = "https://api.github.com/repos/710850609/EasyTier-EUI/releases/latest"
    return github_util.get_latest_version(api_url)

    
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
    try:
        release_infos = get_release_info({'refresh': 'true'})
    except Exception as e:
        logging.exception(f"获取release信息失败，尝试使用本地缓存")
        release_infos = get_release_info({'refresh': 'false'})

    latest_info = release_infos.get('latest_release', {}) if is_release else release_infos.get('latest_prerelease', {})
    asset = latest_info.get('assets', {}).get(f"{sys_name}-{arch_name}", {})
    download_url = asset.get('download_url', '')
    if not download_url or download_url == '':
        raise HttpResponse(f"没有可下载链接")
    return download_url, download_url.split('/')[-1]

if __name__ == '__main__':
    run_configs.setup_env()
    get_release_info({'refresh': 'true'})
    # __get_download_url(True)