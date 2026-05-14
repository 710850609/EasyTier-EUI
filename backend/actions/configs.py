#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import shutil
from pathlib import Path

import tomlkit

from actions import services
from http_dispatcher.dispatcher import HttpException
from http_dispatcher.dispatcher import HttpResponse
from utils import et_run_info
from utils import run_configs
from utils import security
from utils.validators import Validator


def list_config_files(*kwargs):
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

def list_config_status(*kwargs):
    config_files = list_config_files()
    result = []
    for profile in config_files:
        try:
            running = services.status(profile)
            profile['running'] = running
        except Exception as e:
            logging.warning(f'[list_config_status] status check failed for {profile}: {e}')
            profile['running'] = False
        result.append(profile)
    return result

def delete(params, *kwargs):
    profile, _ = Validator.not_empty(params, 'profile', '配置不能为空')
    profile = Validator.check_profile(profile)
    if services.status(params):
        logging.info(f"{profile} 配置运行中，停止服务...")
        services.stop(params)
    info = et_run_info.get(profile)
    if info and info.autostart:
        # 禁用自启，当删除最后一个配置时，触发卸载注册服务
        services.auto_start({'profile': profile, 'enabled': False})
    Path(run_configs.et_config_file(profile)).unlink(missing_ok=True)
    et_run_info.remove(profile)


def rename(params, *kwargs):
    old_profile, _ = Validator.not_empty(params, 'oldProfile', '旧配置名空')
    new_profile, _ = Validator.not_empty(params, 'newProfile', '新配置名空')
    old_profile = Validator.check_profile(old_profile)
    new_profile = Validator.check_profile(new_profile, check_exists=False)
    if old_profile == new_profile:
        logging.warning(f"新旧名称一致，跳过重命名: {old_profile}")
        return {'name': new_profile.replace('.toml', ''), 'profile': new_profile}
    old_config = run_configs.et_config_file(old_profile)
    new_config = run_configs.et_config_file(new_profile)
    if Path(new_config).exists():
       raise HttpException(f"新名称已存在: {new_profile}")

    shutil.copy2(old_config, new_config)
    try:
        services.rename_profile(old_profile, new_profile)
        Path(old_config).unlink(missing_ok=True)
    except Exception as e:
        Path(new_config).unlink(missing_ok=True)
        raise e
    return {'name': new_profile.replace('.toml', ''), 'profile': new_profile}

def save(data, *kwargs):
    profile = data.pop('_profile', None) if data else None
    profile = Validator.check_profile(profile, check_exists=False)
    et_config_file = run_configs.et_config_file(profile)
    path_config_file = Path(et_config_file)
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
    et_run_info.save(profile, None, False, False)


def save_toml(data: str, *kwargs):
    try:
        profile = data.pop('_profile', None) if data else None
        if not profile:
            raise HttpException("profile is none for save toml")
        else:
            # 安全验证
            safe_profile = security.validate_profile(profile)
            if not safe_profile:
                logging.warning(f"无效的配置文件名: {profile}")
                raise HttpException(f"无效的配置文件名: {profile}")
            profile = safe_profile
        doc = tomlkit.parse(data['toml'])
        doc['instance_name'] = profile
        et_config_file = run_configs.et_config_file(profile)
        Path(et_config_file).parent.mkdir(parents=True, exist_ok=True)
        with open(et_config_file, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(doc))
        et_run_info.save(safe_profile, None, False, False)
    except Exception as e:
        logging.error(f"解析配置字符串失败: {e}")
        raise e

def get(params, *kwargs):
    # 同时支持驼峰和下划线参数
    profile, _ = Validator.not_empty(params, 'profile', '未指定配置')
    profile = Validator.check_profile(profile)
    et_config_file = run_configs.et_config_file(profile)
    if os.path.exists(et_config_file):
        with open(et_config_file, "r", encoding="utf-8") as f:
            doc = tomlkit.parse(f.read())
            return doc
    return {}

def get_toml(params=None, *kwargs):
    profile, _ = Validator.not_empty(params, 'profile', '未指定配置')
    profile = Validator.check_profile(profile)
    et_config_file = run_configs.et_config_file(profile)
    with open(et_config_file, "r", encoding="utf-8") as f:
        return f.read()

def download_share_config(params=None, *kwargs):
    profile, _ = Validator.not_empty(params, 'profile', '未指定配置')
    profile = Validator.check_profile(profile)
    tmp_file = copy(profile)
    logging.info(f"{tmp_file}")
    return HttpResponse(file=tmp_file, download_name="config.toml")

def get_share_config_str(params=None, *kwargs):
    profile, _ = Validator.not_empty(params, 'profile', '未指定配置')
    profile = Validator.check_profile(profile)
    tmp_file = copy(profile)
    with open(tmp_file, "r", encoding="utf-8") as f:
        return f.read()

def copy(profile:str):
    profile = Validator.check_profile(profile)
    tmp_file = run_configs.data_dir() + '/tmp/config-copy.toml'
    
    # 确保目录存在
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)

    et_config_file = run_configs.et_config_file(profile)
    with open(et_config_file, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())
    # 情况IP
    doc["ipv4"] = ""
    # 设置启用DHCP
    doc["dhcp"] = True

    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))
    return tmp_file


def __deep_merge(base, override):
    """深度合并两个字典，override 中的值会覆盖 base 中的值"""
    for key, value in override.items():
        # 跳过 null 值，不写入 TOML
        if value is None:
            base.pop(key, None)
            continue
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            __deep_merge(base[key], value)
        else:
            base[key] = value
    return base    
