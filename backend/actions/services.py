#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os.path
import sys
from pathlib import Path
from typing import Union

from http_dispatcher.dispatcher import HttpException
from utils import check_peers, common_util
from utils import process_util
from utils import run_configs
from utils import et_run_info
from utils import fn_service
from utils.process_util import ProcessManager

# 延迟初始化：使用单例模式
_pm = {}
_ext = ".exe" if sys.platform == "win32" else ""

def _get_process_manager(profile:str = None) -> Union[ProcessManager]:
    """获取 ProcessManager 实例（延迟初始化）"""
    global _pm
    pm_key = 'default' if profile is None else profile
    cur_pm = _pm.get(pm_key)
    if cur_pm is None:
        pid_file = run_configs.et_pid_file(profile)
        cur_pm = process_util.ProcessManager(pid_file)
        _pm[pm_key] = cur_pm
    return cur_pm

def status(params=None, *kwargs):
    if params is None:
        params = {}
    profile = params.get('profile')
    info = et_run_info.get(profile)
    if info is not None and info.use_system_service:
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} -o json --rpc-portal {info.rpc_portal} peer"
        result = common_util.run_cmd(cmd)
        is_run_service = result.find('failed to connect to server') < 0
        is_run_profile = result.find('No instance matches the selector') < 0
        return is_run_service and is_run_profile
    else:
        pm = _get_process_manager(profile)
        return pm.status()


def stop(params=None, *kwargs):
    if params is None:
        params = {}
    profile = params.get('profile')
    logging.info('停止ET服务...')
    info = et_run_info.get(profile)
    if info is not None and info.use_system_service:
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service stop"
        common_util.run_cmd(cmd)
    else:
        pm = _get_process_manager(profile)
        pm.stop()

def start(params=None, *kwargs):
    if params is None:
        params = {}
    profile = params.get('profile')
    config_file = run_configs.et_config_file(profile)
    if not Path(config_file).exists():
        raise HttpException(f"不存在配置文件，请先确认配置")
    logging.info('启动ET服务')

    info = et_run_info.get(profile)
    if info is not None and info.use_system_service:
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service start"
        result = common_util.run_cmd(cmd)
        logging.info(f"启动系统注册服务结果：{result}")
        et_run_info.save(profile, info.rpc_portal, info.autostart, True)
    else:
        rpc_port = check_peers.get_available_port(start_port=16888)
        rpc_portal = f"127.0.0.1:{rpc_port}"
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-core')}{_ext} --config-file {config_file} --rpc-portal {rpc_portal}"
        logging.info(f"启动命令: {cmd}")
        pm = _get_process_manager(profile)
        pm.start(cmd)
        autostart = False if info is None else info.autostart
        et_run_info.save(profile, rpc_portal, autostart, False)

def restart(params=None, *kwargs):
    logging.info(f"重启ET服务...")
    if status(params):
       stop(params)
    start(params)

def start_all(*kwargs):
    config_file_list = run_configs.et_config_files()
    if len(config_file_list) == 0:
        logging.info("暂无配置文件，跳过启动服务")
        return
    infos = et_run_info.all()
    system_service_profiles = []
    for _, info in infos.items():
        if info.use_system_service:
            system_service_profiles.append(info.profile)
        elif info.autostart:
            logging.info(f"启动 EaysTier 核心服务：{info.profile}")
            start({'profile': info.profile})
    if len(system_service_profiles) > 0:
        logging.info(f"启动 EaysTier 系统注册服务：{system_service_profiles}")
        start({'profile': system_service_profiles[0]})

def stop_all(*kwargs):
    infos = et_run_info.all()
    system_service_profile = None
    for _, info in infos.items():
        if info.use_system_service:
            system_service_profile = info.profile
        elif info.autostart:
            logging.info(f"停止 EaysTier 核心服务：{info.profile}")
            stop({'profile': info.profile})
    if system_service_profile:
        logging.info(f"停止 EaysTier 系统注册服务")
        stop({'profile': system_service_profile})

def system_service(params=None, *kwargs):
    params = params or {}
    profile = params.get('profile')
    is_enabled = params.get('enabled', False)
    if isinstance(is_enabled, str):
        is_enabled = is_enabled.lower() == 'true'
    if not profile:
        raise HttpException('缺少配置名称')
    config_file = run_configs.et_config_file(profile)
    if not Path(config_file).exists():
        raise HttpException(f'配置文件不存在: {profile}')
    info = et_run_info.get(profile)
    rpc_portal = info.rpc_portal if info else '127.0.0.1:16888'
    autostart = info.autostart if info else False
    if is_enabled:
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service install --config-file {config_file}"
        result = common_util.run_cmd(cmd)
        logging.info(f"注册系统服务结果：{result}")
        et_run_info.save(profile, rpc_portal, autostart, True)
    else:
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service uninstall"
        result = common_util.run_cmd(cmd)
        logging.info(f"卸载系统服务结果：{result}")
        et_run_info.save(profile, rpc_portal, autostart, False)
    return {'success': True, 'enabled': is_enabled}

def auto_start(params=None, *kwargs):
    params = params or {}
    profile = params.get('profile')
    is_enabled = params.get('enabled', False)
    if isinstance(is_enabled, str):
        is_enabled = is_enabled.lower() == 'true'
    if not profile:
        raise HttpException('缺少配置名称')
    info = et_run_info.get(profile)
    info.autostart = True
    # 如果是飞牛，则不注册系统服务
    if fn_service.is_fn_system():
        info.use_system_service = False
    else:
        info.use_system_service = True
    et_run_info.save(*info.__dict__.values())



if __name__ == '__main__':
    # os.symlink("F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/default.toml", "F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/setup/default.toml", target_is_directory=False)
    os.symlink("F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/测试.toml", "F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/setup/测试.toml", target_is_directory=False)