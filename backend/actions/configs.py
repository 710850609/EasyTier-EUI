#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import shutil
from pathlib import Path

import tomlkit
from tomlkit import document

from actions import services
from http_dispatcher.dispatcher import HttpException
from http_dispatcher.dispatcher import HttpResponse
from locales import get_message
from utils import et_run_info, ip_util
from utils import run_configs
from utils import security
from utils.validators import Validator

logger = logging.getLogger(__name__)


def list_lan_ips(*args, **kwargs):
    ips = ip_util.get_lan_ips()
    ip_list = []
    ip_24list = []
    for item in ips:
        ip = item['ip']
        arr = ip.split('.')
        ip_24list.append(f"{arr[0]}.{arr[1]}.{arr[2]}.1/32")
        ip_24list.append(f"{arr[0]}.{arr[1]}.{arr[2]}.0/24")
    return ip_24list + ip_list

def list_config_files(*args, **kwargs):
    config_files = run_configs.et_config_files()
    result = []
    for profile in config_files:
        name = Path(profile).stem
        info = et_run_info.get(profile)
        result.append({
            'name': name,
            'profile': profile,
            'autostart': info.autostart if info else False,
        })
    return result

def list_config_status(*args, **kwargs):
    config_files = list_config_files()
    result = []
    for profile in config_files:
        try:
            running = services.status(profile)
            profile['running'] = running
        except Exception as e:
            logger.warning(f'[list_config_status] status check failed for {profile}: {e}')
            profile['running'] = False
        result.append(profile)
    return result

def delete(params, *args, **kwargs):
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    if services.status(params):
        logger.info(f"{profile} 配置运行中，停止服务...")
        services.stop(params)
    info = et_run_info.get(profile)
    if info and info.autostart:
        # 禁用自启，当删除最后一个配置时，触发卸载注册服务
        services.auto_start({'profile': profile, 'enabled': False})
    Path(run_configs.et_config_file(profile)).unlink(missing_ok=True)
    et_run_info.remove(profile)


def rename(params, *args, **kwargs):
    old_profile, _ = Validator.not_empty(params, 'oldProfile', 'config.old_profile_empty')
    new_profile, _ = Validator.not_empty(params, 'newProfile', 'config.new_profile_empty')
    old_profile = Validator.check_profile(old_profile)
    new_profile = Validator.check_profile(new_profile, check_exists=False)
    if old_profile == new_profile:
        logger.warning(f"新旧名称一致，跳过重命名: {old_profile}")
        return {'name': new_profile.replace('.toml', ''), 'profile': new_profile}
    old_config = run_configs.et_config_file(old_profile)
    new_config = run_configs.et_config_file(new_profile)
    if Path(new_config).exists():
       raise HttpException(get_message('config.name_exists', name=new_profile))

    shutil.copy2(old_config, new_config)
    try:
        services.rename_profile(old_profile, new_profile)
        Path(old_config).unlink(missing_ok=True)
    except Exception as e:
        Path(new_config).unlink(missing_ok=True)
        raise e
    return {'name': new_profile.replace('.toml', ''), 'profile': new_profile}

def save(data, *args, **kwargs):
    profile = data.pop('_profile', None) if data else None
    profile = Validator.check_profile(profile, check_exists=False)
    new_config = data.pop('_new_config', True) if data else True
    et_config_file = run_configs.et_config_file(profile)
    path_config_file = Path(et_config_file)
    if new_config:
        try_count = 0
        profile_name = profile.replace('.toml', '')
        while path_config_file.exists():
            try_count += 1
            profile = f"{profile_name}-{try_count}.toml"
            et_config_file = run_configs.et_config_file(profile)
            path_config_file = Path(et_config_file)
            logger.info(f"存在同名配置，尝试使用配置名称: {et_config_file}")

    if not path_config_file.exists():
        path_config_file.parent.mkdir(parents=True, exist_ok=True)
        path_config_file.touch()
    with open(et_config_file, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())
    if not doc.get("network_identity"):
        doc["network_identity"] = {"network_name": '', "network_secret": ''}
    __deep_merge(doc, data)
    doc['instance_name'] = profile
    # 头部注释
    with open(et_config_file, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))
    #
    et_run_info.save(profile, None, None, None)
    logger.info(f"save profile: {profile}")
    return {'profile': profile}


def save_toml(data: str, *args, **kwargs):
    try:
        profile = data.pop('_profile', None) if data else None
        if not profile:
            raise HttpException(get_message('config.profile_required_for_save'))
        else:
            # 安全验证
            safe_profile = security.validate_profile(profile)
            if not safe_profile:
                logger.warning(get_message('config.invalid_name', profile=profile))
                raise HttpException(get_message('config.invalid_name', profile=profile))
            profile = safe_profile
        doc = tomlkit.parse(data['toml'])
        doc['instance_name'] = profile
        et_config_file = run_configs.et_config_file(profile)
        Path(et_config_file).parent.mkdir(parents=True, exist_ok=True)
        with open(et_config_file, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(doc))
        et_run_info.save(safe_profile, None, None, None)
    except Exception as e:
        logger.error(f"解析配置字符串失败: {e}")
        raise e

def get(params, *args, **kwargs):
    # 同时支持驼峰和下划线参数
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    et_config_file = run_configs.et_config_file(profile)
    if os.path.exists(et_config_file):
        with open(et_config_file, "r", encoding="utf-8") as f:
            doc = tomlkit.parse(f.read())
            return doc
    return {}

def get_toml(params=None, *args, **kwargs):
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    et_config_file = run_configs.et_config_file(profile)
    with open(et_config_file, "r", encoding="utf-8") as f:
        return f.read()

def download_share_config(params=None, *args, **kwargs):
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    tmp_file = copy(profile)
    logger.info(f"{tmp_file}")
    return HttpResponse(file=tmp_file, download_name="config.toml")

def get_share_config_str(params=None, *args, **kwargs):
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    tmp_file = copy(profile)
    with open(tmp_file, "r", encoding="utf-8") as f:
        return f.read()

def copy(profile:str):
    profile = Validator.check_profile(profile)
    tmp_file = run_configs.data_dir() + '/download/temp/config-copy.toml'
    
    # 确保目录存在
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)

    et_config_file = run_configs.et_config_file(profile)
    with open(et_config_file, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())

    share_doc = document()
    # share_doc.add(comment(get_message('config.share_comment', datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
    # 仅拷贝必要的配置项
    share_doc["ipv4"] = ""
    share_doc["dhcp"] = True
    share_doc["network_identity"] = doc.get("network_identity") or {}
    share_doc["peer"] = doc.get("peer") or []


    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(share_doc))
    return tmp_file


def parse_toml(data, *args, **kwargs):
    raw_toml = data.get('toml', '') if data else ''
    if not raw_toml or not raw_toml.strip():
        raise HttpException(get_message('config.toml_empty'))
    try:
        doc = tomlkit.parse(raw_toml)
        return doc
    except Exception as e:
        logger.error(f"解析TOML字符串失败: {e}")
        raise HttpException(get_message('config.toml_parse_error', error=str(e)))


def __deep_merge(base, override):
    """深度合并两个字典，override 中的值会覆盖 base 中的值"""
    for key, value in override.items():
        if value is None:
            base.pop(key, None)
            continue
        if isinstance(value, dict):
            if key not in base or not isinstance(base[key], dict):
                base[key] = tomlkit.table()
            __deep_merge(base[key], value)
        else:
            base[key] = value
    return base