#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import logging
import os.path
import sys
from pathlib import Path
from typing import List, Optional, Set

from et_adapters import get_facade
from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import common_util
from utils import et_run_info
from utils import run_configs
from utils.validators import Validator

logger = logging.getLogger(__name__)

def status(params=None, *args, **kwargs) -> bool:
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    try:
        return get_facade().status(profile)
    except Exception:
        return False

def stop(params=None, *args, **kwargs):
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    get_facade().stop_network(profile)

def start(params=None, *args, **kwargs):
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    config_file = run_configs.et_config_file(profile)
    if not Path(config_file).exists():
        raise HttpException(get_message('service.config_not_found'))
    get_facade().start_network(config_file, profile)

def restart(params=None, *args, **kwargs):
    logger.info(f"重启ET服务...")
    if status(params):
       stop(params)
    start(params)

def start_all(*args, **kwargs):
    config_file_list = run_configs.et_config_files()
    if len(config_file_list) == 0:
        logger.info("暂无配置文件，跳过启动服务")
        return
    infos = et_run_info.get_all()
    system_service_profiles = []
    for _, info in infos.items():
        if info.use_system_service:
            try:
                system_service_profiles.append(info.profile)
            except Exception as e:
                logger.exception(f"启动【{info.profile}】失败")
        elif info.autostart:
            logger.info(f"启动 EaysTier 核心服务：{info.profile}")
            start({'profile': info.profile})
    if len(system_service_profiles) > 0:
        logger.info(f"启动 EaysTier 系统注册服务：{system_service_profiles}")
        start({'profile': system_service_profiles[0]})

def stop_all(*args, **kwargs) -> List[str]:
    stop_profiles = []
    infos = et_run_info.get_all()
    system_service_profile = None
    for _, info in infos.items():
        if status({'profile': info.profile}):
            if info.use_system_service:
                system_service_profile = info.profile
            else:
                logger.info(f"停止 EaysTier 核心服务：{info.profile}")
                stop({'profile': info.profile})
            stop_profiles.append(info.profile)
    if system_service_profile:
        logger.info(f"停止 EaysTier 系统注册服务")
        stop({'profile': system_service_profile})
    logger.info(f"停止配置：{stop_profiles}")
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
        logger.info(f"开启自启未变更，跳过修改：{info.autostart}")
        return
    # 提前获取状态
    is_running = status(params)
    info.autostart = is_enabled
    info.use_system_service = is_enabled
    facade = get_facade()
    service_adapter = facade.get_service_adapter()
    if service_adapter is None:
        # 不支持系统服务，仅修改配置
        info.use_system_service = False
        et_run_info.save(*info.__dict__.values())
        return
    # 支持系统服务
    auto_start_set = __get_system_service_profiles()
    if is_enabled and profile not in auto_start_set:
        auto_start_set.add(profile)
    if not is_enabled and profile in auto_start_set:
        auto_start_set.remove(profile)

    if is_running:
        # 用stop方法，兼容在运行的非自启服务
        stop(params)
    service_status = service_adapter.system_service_status()
    if len(auto_start_set) > 0:
        rpc_portal = service_adapter.system_service_install(list(auto_start_set), info.log_level)
        info.rpc_portal = rpc_portal
    elif service_status > -1:
        logger.info(f"不存在需要自启配置，卸载系统服务")
        if service_status == 1:
            logger.info(f"停止系统服务...")
            service_adapter.stop_network('')
        service_adapter.system_service_uninstall()
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
    service_adapter = get_facade().get_service_adapter()
    if service_adapter is None or old_profile not in auto_start_set:
        # 不支持系统服务环境 或是 旧配置不是开机自启，忽略处理
        et_run_info.save(new_profile, old_info.rpc_portal, old_info.autostart, old_info.use_system_service, old_info.log_level)
        et_run_info.remove(old_profile)
    else:
        is_running = service_adapter.system_service_status() == 1
        is_save_new = False
        try:
            if is_running:
                service_adapter.stop_network('')
            auto_start_set.remove(old_profile)
            auto_start_set.add(new_profile)
            et_run_info.save(new_profile, None, old_info.autostart, old_info.use_system_service, old_info.log_level)
            is_save_new = True
            rpc_portal = service_adapter.system_service_install(list(auto_start_set), old_info.log_level)
            et_run_info.save(new_profile, rpc_portal, True, True)
            et_run_info.remove(old_profile)
        except Exception as e:
            if is_save_new:
                et_run_info.remove(new_profile)
            raise e

# def change_log_level(log_level):
    # infos = et_run_info.get_all()
    # profiles_systemed = []
    # need_handle_profiles_no_systemed = []
    # need_handle_systemed = False
    # for info in infos.values():
    #     if status({'profile': info.profile}):
    #         if not info.use_system_service:
    #             need_handle_profiles_no_systemed.append(info.profile)
    #         else:
    #             need_handle_systemed = True
    #     if info.use_system_service:
    #         profiles_systemed.append(info.profile)
    # service_adapter = get_facade().get_service_adapter()
    # if service_adapter is None:
    #     return
    # # 处理系统服务
    # if len(profiles_systemed) > 0:
    #     if need_handle_systemed:
    #         service_adapter.stop_network('')
    #     service_adapter.system_service_uninstall()
    #     service_adapter.system_service_install(profiles_systemed, log_level)
    #     if need_handle_systemed:
    #         service_adapter.start_network('', '')
    # # 处理非系统服务
    # for profile in need_handle_profiles_no_systemed:
    #     info = et_run_info.get(profile)
    #     log_level = 'disabled' if log_level == 'off' else log_level
    #     log_level = 'warning' if log_level == 'warn' else log_level
    #     _ext = ".exe" if sys.platform == "win32" else ""
    #     cmd = [
    #         f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext}",
    #         "--rpc-portal",
    #         info.rpc_portal,
    #         "logger",
    #         "set",
    #         log_level,
    #     ]
    #     logger.info(f"设置日志级别命令： {cmd}")
    #     common_util.run_cmd(cmd)


def __get_system_service_profiles() -> Set[str]:
    auto_start_set = set()
    for config_file, item in et_run_info.get_all().items():
        if item.autostart:
            if Path(run_configs.et_config_file(config_file)).exists():
                auto_start_set.add(config_file)
            else:
                logger.warning(f"跳过并移除不存在的配置: {config_file}")
                et_run_info.remove(config_file)
    return auto_start_set