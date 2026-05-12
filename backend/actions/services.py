#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os.path
import sys
from pathlib import Path
from typing import Union, List

from http_dispatcher.dispatcher import HttpException
from utils import check_peers, common_util
from utils import process_util
from utils import run_configs
from utils import et_run_info
from utils import fn_service
from utils.process_util import ProcessManager
from utils import security

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
    if profile:
        safe_profile = security.validate_profile(profile)
        if not safe_profile:
            logging.warning(f"无效的配置文件名: {profile}")
            raise HttpException('无效的配置文件名')
        profile = safe_profile
    info = et_run_info.get(profile)
    if info is not None and info.use_system_service:
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} -o json -p {info.rpc_portal} -m {profile} peer"
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
    if profile:
        safe_profile = security.validate_profile(profile)
        if not safe_profile:
            logging.warning(f"无效的配置文件名: {profile}")
            raise HttpException('无效的配置文件名')
        profile = safe_profile
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
    if profile:
        safe_profile = security.validate_profile(profile)
        if not safe_profile:
            logging.warning(f"无效的配置文件名: {profile}")
            raise HttpException('无效的配置文件名')
        profile = safe_profile
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
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-core')}{_ext} -c {config_file} -r {rpc_portal}"
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

def auto_start(params=None, *kwargs):
    params = params or {}
    profile = params.get('profile')
    if profile:
        safe_profile = security.validate_profile(profile)
        if not safe_profile:
            logging.warning(f"无效的配置文件名: {profile}")
            raise HttpException('无效的配置文件名')
        profile = safe_profile
    if not profile:
        raise HttpException('缺少配置名称')
    is_enabled = params.get('enabled', False)
    if isinstance(is_enabled, str):
        is_enabled = is_enabled.lower() == 'true'
    info = et_run_info.get(profile)
    info.autostart = is_enabled
    info.use_system_service = is_enabled
    # 如果是飞牛，则不注册系统服务
    if fn_service.is_fn_system():
        info.use_system_service = False
    else:
        service_profiles = set()
        for profile, item in et_run_info.all().items():
            if item.autostart:
                if Path(run_configs.et_config_file(profile)).exists():
                    service_profiles.add(profile)
                else:
                    logging.warning(f"跳过并移除不存在的配置: {profile}")
                    et_run_info.remove(profile)
        if not is_enabled and profile in service_profiles:
            service_profiles.remove(profile)
        service_status = _system_service_status()
        if len(service_profiles) > 0:
            rpc_portal = _system_service_install(list(service_profiles))
            info.rpc_portal = rpc_portal
        elif service_status > -1:
            logging.info(f"不存在需要自启配置，卸载系统服务")
            if service_status == 1:
                _system_service_stop()
            _system_service_uninstall()
        else:
            pass
    et_run_info.save(*info.__dict__.values())


def _system_service_install(profiles: List[str] = []) -> str:
    if len(profiles or []) == 0:
        logging.info("未指定启动配置，跳过注册系统服务")
        return
    cmd_config_file_parts = ''
    for profile in profiles:
        cfg_path = run_configs.et_config_file(profile)
        if not Path(cfg_path).exists():
            raise HttpException(f"配置不存在: {profile}")
        cmd_config_file_parts += f" -c {cfg_path}"
    desc = f"易组网-启动配置:{','.join(profiles)}"
    display_name = "EasyTier-Lite"
    rpc_port = check_peers.get_available_port(start_port=16999)
    rpc_portal = f"127.0.0.1:{rpc_port}"
    cmd = (f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service install "
           f' --display-name {display_name}'
           f' --description {desc}'
           f" --core-path {run_configs.core_dir()}"
           f" --service-work-dir {run_configs.data_dir()}"
           f" --rpc-portal {rpc_portal}"
           f" --file-log-level error"
           f" --file-log-dir {run_configs.log_dir()}"
           f" {cmd_config_file_parts}")
    logging.info(f"注册服务命令： {cmd}")
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务注册结果：{result}")
    for profile in profiles:
        p = et_run_info.get(profile)
        p.rpc_portal = rpc_portal
        et_run_info.save(*p.__dict__.values())
    return rpc_portal

def _system_service_uninstall():
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service uninstall"
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务卸载结果：{result}")
    pass

def _system_service_start():
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service start"
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务启动结果：{result}")
    pass

def _system_service_status() -> int:
    """
    -1: 未注册
    0：未运行
    1：运行中
    """
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service status"
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务运行状态：{result}")
    if result.find('stopped') > 0:
        return 0
    elif result.find('running') > 0:
        return 1
    elif result.find('not installed') > 0:
        return -1
    else:
        raise HttpException(f"未知服务状态： {result}")
    pass

def _system_service_stop():
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service stop"
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务停止结果：{result}")
    pass


if __name__ == '__main__':
    # os.symlink("F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/default.toml", "F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/setup/default.toml", target_is_directory=False)
    os.symlink("F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/测试.toml", "F:/git-space/EasyTier-Lite/temp/EasyTier-Lite/config/setup/测试.toml", target_is_directory=False)