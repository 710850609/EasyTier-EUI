#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import logging
import os.path
import sys
import threading
from pathlib import Path
from typing import Union, List, Optional, Set

from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import check_peers, common_util
from utils import et_run_info
from utils import process_util
from utils import run_configs
from utils.process_util import ProcessManager
from utils.validators import Validator

try:
    from utils.et_bridge import et_bridge
    _FFI_AVAILABLE = True
except Exception:
    et_bridge = None
    _FFI_AVAILABLE = False

# 延迟初始化：使用线程安全的单例模式
_pm = {}
_pm_lock = threading.Lock()
_ext = ".exe" if sys.platform == "win32" else ""

def _get_process_manager(profile:str = None) -> Union[ProcessManager]:
    """获取 ProcessManager 实例（延迟初始化，线程安全）"""
    if not profile:
        raise HttpException('validate.profile_required')
    pm_key = profile
    
    # 双重检查锁定模式，保证线程安全的同时提高性能
    cur_pm = _pm.get(pm_key)
    if cur_pm is not None:
        return cur_pm
    
    with _pm_lock:
        # 再次检查，防止在获取锁期间已被其他线程创建
        cur_pm = _pm.get(pm_key)
        if cur_pm is None:
            pid_file = run_configs.et_pid_file(profile)
            cur_pm = process_util.ProcessManager(pid_file.replace('.toml', ''))
            _pm[pm_key] = cur_pm
    return cur_pm

def status(params=None, *args, **kwargs) -> bool:
    if run_configs.IS_ANDROID:
        if not _FFI_AVAILABLE or et_bridge is None or et_bridge._lib is None:
            return False
        try:
            instances = et_bridge.list_instance(10)
            return len(instances) > 0
        except Exception:
            return False
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    info = et_run_info.get(profile)
    if info is not None and info.use_system_service:
        return _system_service_status() == 1
    else:
        pm = _get_process_manager(profile)
        return pm.status()

def stop(params=None, *args, **kwargs):
    if run_configs.IS_ANDROID:
        if not _FFI_AVAILABLE or et_bridge is None or et_bridge._lib is None:
            return
        try:
            et_bridge.stop_all_instances()
            logging.info("Android: Stopped all EasyTier instances via FFI")
        except Exception as e:
            logging.warning(f"Android: Failed to stop instances: {e}")
        return
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    info = et_run_info.get(profile)
    if info is not None and info.use_system_service:
        if _system_service_status() == -1:
            logging.warning(f"未注册ET系统服务，跳过停止服务")
            return
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service stop"
        logging.info(f"停止ET服务: {cmd}")
        common_util.run_cmd(cmd)
    else:
        logging.info(f"停止ET配置: {profile}")
        pm = _get_process_manager(profile)
        pm.stop()

def start(params=None, *args, **kwargs):
    if run_configs.IS_ANDROID:
        if not _FFI_AVAILABLE or et_bridge is None or et_bridge._lib is None:
            raise HttpException(get_message('service.not_supported_android'))
        profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
        config_file = run_configs.et_config_file(profile)
        if not Path(config_file).exists():
            raise HttpException(get_message('service.config_not_found'))
        with open(config_file, 'r', encoding='utf-8') as f:
            toml_config = f.read()
        ret = et_bridge.parse_config(toml_config)
        if ret != 0:
            raise HttpException(f"Config parse failed: {et_bridge.get_last_error()}")
        ret = et_bridge.run_network_instance(toml_config)
        if ret != 0:
            raise HttpException(f"Failed to start instance: {et_bridge.get_last_error()}")
        logging.info(f"Android: Started EasyTier instance '{profile}' via FFI")
        return
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    config_file = run_configs.et_config_file(profile)
    if not Path(config_file).exists():
        raise HttpException(get_message('service.config_not_found'))

    info = et_run_info.get(profile)
    if info is not None and info.use_system_service:
        if _system_service_status() == -1:
            raise HttpException(get_message('service.not_registered'))
        cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service start"
        logging.info(f"启动ET服务: {cmd}")
        result = common_util.run_cmd(cmd)
        logging.info(f"启动系统注册服务结果：{result}")
        et_run_info.save(profile, info.rpc_portal, info.autostart, True)
    else:
        rpc_port = check_peers.get_available_port(start_port=16888)
        rpc_portal = f"127.0.0.1:{rpc_port}"
        # 使用用列表传参，避免执行文件路径含空格，导致报错找不到文件
        cmd = [
            f"{os.path.join(run_configs.core_dir(), 'easytier-core')}{_ext}",
            "-c",
            config_file,
            "-r",
            rpc_portal,
            f"--file-log-dir", f"{run_configs.log_dir()}",
            f"--file-log-level", f"{info.log_level or 'error'}",
            f"--file-log-size", f"50"  # 单个文件日志大小，单位 MB，默认值为 100MB
        ]
        logging.info(f"启动ET命令: {cmd}")
        pm = _get_process_manager(profile)
        pm.start(cmd)
        autostart = False if info is None else info.autostart
        et_run_info.save(profile, rpc_portal, autostart, False)

def restart(params=None, *args, **kwargs):
    logging.info(f"重启ET服务...")
    if status(params):
       stop(params)
    start(params)

def start_all(*args, **kwargs):
    config_file_list = run_configs.et_config_files()
    if len(config_file_list) == 0:
        logging.info("暂无配置文件，跳过启动服务")
        return
    infos = et_run_info.get_all()
    system_service_profiles = []
    for _, info in infos.items():
        if info.use_system_service:
            try:
                system_service_profiles.append(info.profile)
            except Exception as e:
                logging.exception(f"启动【{info.profile}】失败")
        elif info.autostart:
            logging.info(f"启动 EaysTier 核心服务：{info.profile}")
            start({'profile': info.profile})
    if len(system_service_profiles) > 0:
        logging.info(f"启动 EaysTier 系统注册服务：{system_service_profiles}")
        start({'profile': system_service_profiles[0]})

def stop_all(*args, **kwargs) -> List[str]:
    if run_configs.IS_ANDROID:
        if not _FFI_AVAILABLE or et_bridge is None or et_bridge._lib is None:
            return []
        try:
            instances = et_bridge.list_instance(10)
            et_bridge.stop_all_instances()
            logging.info("Android: Stopped all instances via FFI")
            return list(instances.keys())
        except Exception as e:
            logging.warning(f"Android: Failed to stop all: {e}")
            return []
    stop_profiles = []
    infos = et_run_info.get_all()
    system_service_profile = None
    for _, info in infos.items():
        if status({'profile': info.profile}):
            if info.use_system_service:
                system_service_profile = info.profile
            else:
                logging.info(f"停止 EaysTier 核心服务：{info.profile}")
                stop({'profile': info.profile})
            stop_profiles.append(info.profile)
    if system_service_profile:
        logging.info(f"停止 EaysTier 系统注册服务")
        stop({'profile': system_service_profile})
    logging.info(f"停止配置：{stop_profiles}")
    return stop_profiles

def auto_start(params: Optional[dict]=None, keep_run_status:bool=True, *args, **kwargs):
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    is_enabled = params.get('enabled', False)
    if isinstance(is_enabled, str):
        is_enabled = is_enabled.lower() == 'true'
    # 深拷贝，避免修改原数据
    info = copy.deepcopy(et_run_info.get(profile))
    if info and info.autostart == is_enabled:
        logging.info(f"开启自启未变更，跳过修改：{info.autostart}")
        return
    # 提前获取状态
    is_running = status(params)
    info.autostart = is_enabled
    info.use_system_service = is_enabled
    if run_configs.is_fn_system() or run_configs.is_docker():
        # 如果是飞牛环境或 Docker 容器环境，则不注册系统服务
        info.use_system_service = False
        et_run_info.save(*info.__dict__.values())
        return
    # 非飞牛系统处理
    auto_start_set = __get_system_service_profiles()
    if is_enabled and profile not in auto_start_set:
        auto_start_set.add(profile)
    if not is_enabled and profile in auto_start_set:
        auto_start_set.remove(profile)

    if is_running:
        # 用stop方法，兼容在运行的非自启服务
        stop(params)
    service_status = _system_service_status()
    if len(auto_start_set) > 0:
        rpc_portal = _system_service_install(list(auto_start_set), info.log_level)
        info.rpc_portal = rpc_portal
    elif service_status > -1:
        logging.info(f"不存在需要自启配置，卸载系统服务")
        if service_status == 1:
            logging.info(f"停止系统服务...")
            _system_service_stop()
        _system_service_uninstall()
    else:
        pass
    et_run_info.save(*info.__dict__.values())
    if is_running and keep_run_status:
        start(params)

def rename_profile(old_profile: Optional[str], new_profile: Optional[str]):
    old_profile = Validator.check_profile(old_profile)
    new_profile = Validator.check_profile(new_profile)
    if not old_profile:
        raise HttpException(get_message('service.config_not_running', old_profile=old_profile))
    auto_start_set = __get_system_service_profiles()
    old_info = et_run_info.get(old_profile)
    if run_configs.is_fn_system() or old_profile not in auto_start_set:
        # 飞牛环境或是旧配置不是开机自启，忽略处理
        et_run_info.save(new_profile, old_info.rpc_portal, old_info.autostart, old_info.use_system_service, old_info.log_level)
        et_run_info.remove(old_profile)
    else:
        is_running = _system_service_status() == 1
        is_save_new = False
        try:
            if is_running:
                _system_service_stop()
            auto_start_set.remove(old_profile)
            auto_start_set.add(new_profile)
            et_run_info.save(new_profile, None, old_info.autostart, old_info.use_system_service, old_info.log_level)
            is_save_new = True
            rpc_portal = _system_service_install(list(auto_start_set), old_info.log_level)
            et_run_info.save(new_profile, rpc_portal, True, True)
            et_run_info.remove(old_profile)
        except Exception as e:
            if is_save_new:
                et_run_info.remove(new_profile)
            raise e

def change_log_level(log_level):
    infos = et_run_info.get_all()
    profiles_systemed = []
    need_handle_profiles_no_systemed = []
    need_handle_systemed = False
    for info in infos.values():
        if status({'profile': info.profile}):
            if not info.use_system_service:
                need_handle_profiles_no_systemed.append(info.profile)
            else:
                need_handle_systemed = True
        if info.use_system_service:
            profiles_systemed.append(info.profile)
    # 处理系统服务
    if len(profiles_systemed) > 0:
        if need_handle_systemed:
            _system_service_stop()
        _system_service_uninstall()
        _system_service_install(profiles_systemed, log_level)
        if need_handle_systemed:
            _system_service_start()
    # 处理非系统服务
    for profile in need_handle_profiles_no_systemed:
        info = et_run_info.get(profile)
        log_level = 'disabled' if log_level == 'off' else log_level
        log_level = 'warning' if log_level == 'warn' else log_level
        cmd = [
            f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext}",
            "--rpc-portal",
            info.rpc_portal,
            "logger",
            "set",
            log_level,
        ]
        logging.info(f"设置日志级别命令： {cmd}")
        common_util.run_cmd(cmd)


def __get_system_service_profiles() -> Set[str]:
    auto_start_set = set()
    for config_file, item in et_run_info.get_all().items():
        if item.autostart:
            if Path(run_configs.et_config_file(config_file)).exists():
                auto_start_set.add(config_file)
            else:
                logging.warning(f"跳过并移除不存在的配置: {config_file}")
                et_run_info.remove(config_file)
    return auto_start_set

def _system_service_install(profiles: List[str], log_level:str = 'error') -> str:
    if len(profiles or []) == 0:
        raise AssertionError(get_message('service.no_config_for_system_service'))
    cmd_config_file_parts = ''
    for profile in profiles:
        cfg_path = run_configs.et_config_file(profile)
        if Path(cfg_path).exists():
            cmd_config_file_parts += f" -c {cfg_path}"
        else:
            logging.warning(f"跳过配置不存在: {profile}")
    desc = get_message('service.start_config_desc') + f":{','.join(profiles)}"
    display_name = "EasyTier-EUI"
    rpc_port = check_peers.get_available_port(start_port=16999)
    rpc_portal = f"127.0.0.1:{rpc_port}"
    cmd = (f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service install "
           f' --display-name {display_name}'
           f' --description {desc}'
           f" --core-path {os.path.join(run_configs.core_dir(), 'easytier-core')}{_ext}"
           f" --service-work-dir {run_configs.data_dir()}"
           f" --rpc-portal {rpc_portal}"
           f" {cmd_config_file_parts}"
           f" --file-log-dir {run_configs.log_dir()}"
           f" --file-log-level {log_level or 'error'}"
           f" --file-log-size 50" # 单个文件日志大小，单位 MB，默认值为 100MB
           )
    logging.info(f"注册服务命令： {cmd}")
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务注册结果：{result}")
    for profile in profiles:
        p = et_run_info.get(profile)
        p.rpc_portal = rpc_portal
        p.autostart = True
        p.use_system_service = True
        et_run_info.save(*p.__dict__.values())
    return rpc_portal

def _system_service_uninstall():
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service uninstall"
    common_util.run_cmd(cmd)

def _system_service_start():
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service start"
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务启动结果：{result}")

def _system_service_stop():
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} service stop"
    result = common_util.run_cmd(cmd)
    logging.info(f"ET系统服务停止结果：{result}")

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
        raise HttpException(get_message('service.unknown_status', status=result))