#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path

import tomlkit

from http_dispatcher.dispatcher import HttpResponse
from http_dispatcher.dispatcher import HttpException
from utils import run_configs
from actions import services
from utils import et_run_info


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
    profile = params.get('profile') if params else None
    if not profile:
        raise HttpException('缺少配置名称')
    config_file = run_configs.et_config_file(profile)
    if not os.path.exists(config_file):
        raise HttpException(f'配置文件不存在: {profile}')
    os.remove(config_file)
    pid_file = run_configs.et_pid_file(None if profile == 'default.toml' else profile.replace('.toml', ''))
    if os.path.exists(pid_file):
        os.remove(pid_file)
    et_run_info.remove(profile)
    return {'success': True}

def rename(params, *kwargs):
    old_profile = params.get('oldProfile') if params else None
    new_name = params.get('newName') if params else None
    if not old_profile or not new_name:
        raise HttpException('缺少参数')
    safe_name = new_name.strip().replace(' ', '_')
    if not safe_name:
        raise HttpException('新名称不能为空')
    new_profile = safe_name if safe_name.endswith('.toml') else f'{safe_name}.toml'
    old_file = run_configs.et_config_file(old_profile)
    new_file = run_configs.et_config_file(new_profile)
    if not os.path.exists(old_file):
        raise HttpException(f'原配置文件不存在: {old_profile}')
    if old_profile != new_profile and os.path.exists(new_file):
        raise HttpException(f'目标配置文件已存在: {safe_name}')
    os.rename(old_file, new_file)
    old_info = et_run_info.get(old_profile)
    if old_info:
        et_run_info.save(new_profile, old_info.rpc_portal, old_info.autostart, old_info.use_system_service)
    return {'name': safe_name, 'profile': new_profile}

def save(data, *kwargs):
    profile = data.pop('_profile', None) if data else None
    if not profile:
        profile = None
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
    if doc.get("rpc_portal") == '':
        doc.pop("rpc_portal")
    # 头部注释
    with open(et_config_file, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))


def save_toml(data: str, *kwargs):
    try:
        profile = data.pop('_profile', None) if data else None
        if not profile:
            profile = None
        doc = tomlkit.parse(data['toml'])
        et_config_file = run_configs.et_config_file(profile)
        Path(et_config_file).parent.mkdir(parents=True, exist_ok=True)
        with open(et_config_file, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(doc))
        # flag_file = run_configs.et_init_flag_file()
        # Path(flag_file).unlink(missing_ok=True)
    except Exception as e:
        logging.error(f"解析配置字符串失败: {e}")
        raise e

def get(params, *kwargs):
    file_name = params.get('fileName') if params else None
    et_config_file = run_configs.et_config_file(file_name)
    if os.path.exists(et_config_file):
        with open(et_config_file, "r", encoding="utf-8") as f:
            doc = tomlkit.parse(f.read())
            return doc
    return {}

def get_toml(params=None, *kwargs):
    profile = params.get('profile') if params else None
    et_config_file = run_configs.et_config_file(profile)
    with open(et_config_file, "r", encoding="utf-8") as f:
        return f.read()

def download(params=None, *kwargs):
    profile = params.get('profile') if params else None
    tmp_file = copy(profile)
    logging.info(f"{tmp_file}")
    return HttpResponse(file=tmp_file, download_name="config.toml")

def copy(profile=None, *kwargs): 
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
