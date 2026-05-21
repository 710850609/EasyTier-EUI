#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path

import requests
import tomlkit

from http_dispatcher.dispatcher import HttpException
from utils import check_peers as check_util, run_configs
from utils import github_util


def check_peers(*kwargs):
    """
    检查节点是否可用
    :param request_data: 请求数据（可选）
    """
    peer_list = public_peers(data = {'refresh': False})
    if len(peer_list) == 0:
        peer_list = public_peers(data = {'refresh': True})
    # 提取 URI 列表
    peer_uris = [peer['uri'] for peer in peer_list]
    core_dir = run_configs.core_dir()
    result = check_util.check_peers(core_dir, peer_uris, max_wait_second=6)
    for peer in peer_list:
        if peer['uri'] in result['success']:
            peer['status'] = 1
        else:
            peer['status'] = 0
    return peer_list


def public_peers(data:dict, *kwargs):
    refresh = data and 'refresh' in data and data['refresh'] or False
    profile = None if data is None else data.get('profile')
    peer_meta = {}
    try:
        peer_meta = __get_public_peers(refresh)
    except Exception as e:
        logging.exception('获取公共节点失败')
        raise HttpException(f"获取公共节点失败，请尝试在设置修改Github加速地址后重试")
    peer_uris = []
    config_file = run_configs.et_config_file(profile)
    if Path(config_file).exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                doc = tomlkit.parse(f.read())
                for i in (doc.get("peer") or []):
                    peer_uris.append(i["uri"])
        except Exception as e:
            logging.error(f"解析配置文件失败: {e}")
            # 配置文件解析失败时，返回空列表，不影响获取公共节点
            pass
    config_peers_set = set(peer_uris)

    for key, item in peer_meta.get("peers", {}).items():
        peer = f"{key}"
        # 过滤未启用：空uri
        if peer not in config_peers_set and len(item.get('uri').strip()) > 0:
            peer_uris.append(peer)
    peers = []
    for uri in peer_uris:
        label = uri
        peers.append({'label': label, 'uri': uri})
    return peers


def __get_public_peers(refresh=False):
    peer_meta_file = run_configs.et_peer_meta_file()
    if refresh or not Path(peer_meta_file).exists():
        return __download_peer_meta()
    else:
        with open(peer_meta_file, "r", encoding="utf-8") as f:
            return json.load(f)

def __download_peer_meta():
    try:
        github_proxy = github_util.get_github_proxy()
        peer_meta_url = f"https://raw.githubusercontent.com/710850609/EasyTier-Lite/refs/heads/main/peers/peer-txt-meta.json"
        if github_proxy and github_proxy != '':
            peer_meta_url = f"{github_proxy}/{peer_meta_url}"
        response = requests.get(peer_meta_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        peer_meta_file = run_configs.et_peer_meta_file()
        with open(peer_meta_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return data
    except Exception as e:
        logging.error(f"获取节点元数据失败: {e}")
        raise    