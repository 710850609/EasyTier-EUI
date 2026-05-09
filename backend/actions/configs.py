#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path

import tomlkit

from http_dispatcher.dispatcher import HttpResponse
from http_dispatcher.dispatcher import HttpException
from utils import run_configs
from actions import et_core
from actions import services


def need_setting(*kwargs):
    if not et_core.check_core():
        raise HttpException('内核不存在，请到【设置-内核】安装内核')
    et_config_file = run_configs.core_dir()
    if not os.path.exists(et_config_file):
        return { "needConfig": True }

    config_files = run_configs.et_config_files()
    return { "needConfig": len(config_files) == 0 }

def list_configs(*kwargs):
    config_files = run_configs.et_config_files()
    result = []
    for profile in config_files:
        name = Path(profile).stem
        try:
            running = services.status({'profile': profile})
        except Exception:
            running = False
        result.append({
            'name': name,
            'profile': profile,
            'running': running or False
        })
    if not result:
        result.append({
            'name': 'default',
            'profile': 'default.toml',
            'running': False
        })
    return result

def save(data, *kwargs):
    et_config_file = run_configs.et_config_file()
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
    # flag_file = run_configs.et_init_flag_file()
    # Path(flag_file).unlink(missing_ok=True)


def save_toml(data: str, *kwargs):
    try:
        # 解析配置字符串
        doc = tomlkit.parse(data['toml'])
        et_config_file = run_configs.et_config_file()
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

def get_toml(*kwargs):
    et_config_file = run_configs.et_config_file()
    with open(et_config_file, "r", encoding="utf-8") as f:
        return f.read()

def download(*kwargs):    
    tmp_file = copy()
    logging.info(f"{tmp_file}")
    return HttpResponse(file=tmp_file, download_name="config.toml")

def copy(*kwargs): 
    tmp_file = run_configs.data_dir() + '/tmp/config-copy.toml'
    
    # 确保目录存在
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)

    et_config_file = run_configs.et_config_file()
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
