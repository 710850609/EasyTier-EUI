#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path

import tomlkit

from http_dispatcher.dispatcher import HttpException
from models.peers import PeersCheckResult
from utils import check_peers as check_util, run_configs
from utils import github_util


def check_peers(params: dict, *kwargs):
    """
    检查节点是否可用
    :param request_data: 请求数据（可选）
    """
    profile = (params or {}).get('profile')
    peer_list = public_peers(data = {'profile': profile, 'refresh': 'false'})
    if len(peer_list) == 0:
        peer_list = public_peers(data = {'profile': profile, 'refresh': 'true'})
    # 提取 URI 列表
    peer_uris = [peer['uri'] for peer in peer_list]
    core_dir = run_configs.core_dir()
    result = check_util.check_peers(core_dir, peer_uris, max_wait_second=6)
    for peer in peer_list:
        success_peers = result.get('success', {})
        uri = peer.get('uri')
        peer_result = success_peers.get(uri, {})
        if uri in success_peers.keys() and peer_result:
            peer['status'] = 1
            # peer['src_uri'] = peer_result.get('src_uri')
            peer['relay'] = peer_result.get('relay')
            peer['latency'] = peer_result.get('latency')
            peer['dynamic'] = peer_result.get('dynamic')
            peer['hostname'] = peer_result.get('hostname')
        else:
            peer['status'] = 0
            peer['relay'] = -1
            peer['latency'] = -1
    __save_peer_check_result(peer_list, sort=True)
    return peer_list


def public_peers(data:dict, *kwargs):
    data = data or {}
    refresh = data.get('refresh', 'false').lower() == 'true'
    profile = data.get('profile')
    peers = __get_public_peers(refresh)
    uri_set = set(item.get('uri') for item in peers)

    config_file = run_configs.et_config_file(profile)
    if Path(config_file).exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                doc = tomlkit.parse(f.read())
                for item in (doc.get("peer") or []):
                    uri = item["uri"]
                    if uri not in uri_set:
                        uri_set.add(uri)
                        peers.insert(0, {'uri': uri, 'src_uri': uri, 'relay': -1, 'latency': -1, 'status': -1 })
        except Exception as e:
            logging.error(f"解析配置文件失败: {e}")
            # 配置文件解析失败时，返回空列表，不影响获取公共节点
            pass
    return peers

def set_peer_source(params: dict, *kwargs):
    params = params or {}
    source = params.get('source', '')
    test_peer_mark_file = Path(run_configs.data_dir(), 'test-peer-source')
    if source.lower() == 'test':
        test_peer_mark_file.touch(exist_ok=True)
        logging.info(f"启用测试节点源")
    else:
        test_peer_mark_file.unlink(missing_ok=True)
        logging.info(f"禁用测试节点源")
    __get_public_peers(refresh=True)

def get_peer_source(*kwargs):
    if Path(run_configs.data_dir(), 'test-peer-source').exists():
        return {'source': 'test'}
    return {'source': ''}


def __get_public_peers(refresh=False) -> list[dict]:
    result :list[PeersCheckResult]= []
    meta_data = None
    peer_meta_file = run_configs.et_peer_meta_file()
    if refresh or not Path(peer_meta_file).exists():
        meta_data = __download_peer_meta()

    peer_check_result_file = run_configs.et_peer_check_result_file()
    if not refresh and Path(peer_check_result_file).exists():
        try:
            with open(peer_check_result_file, "r", encoding="utf-8") as f:
                json_list = json.load(f)
                for item in json_list:
                    result.append(PeersCheckResult(**item))
        except Exception as e:
            logging.error(f"解析节点检查结果失败: {str(e)}")
            result = []
            # 节点检查结果解析失败时，返回空字典，不影响获取公共节点
            pass
    if len(result) > 0:
        peers = [item.__dict__ for item in result]
    else:
        if meta_data is None:
            with open(peer_meta_file, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
        # 转换数据格式
        uri_set = set()
        for uri, item in meta_data.get("peers", {}).items():
            real_uri = item.get('uri', '').strip()
            if len(real_uri) > 0 and uri not in uri_set:
                uri_set.add(uri)
                dynamic = real_uri and uri != real_uri
                result.append(PeersCheckResult(uri, real_uri, dynamic=dynamic))

        peers = [item.__dict__ for item in result]
        __sort_peers(peers)
        with open(peer_check_result_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(peers, ensure_ascii=False, indent=2))

    return peers

def __save_peer_check_result(peers: list[dict|PeersCheckResult], sort: bool=False):
    dict_peers = [item.__dict__ if isinstance(item, PeersCheckResult) else item for item in peers]
    if sort:
        __sort_peers(dict_peers)
    with open(run_configs.et_peer_check_result_file(), "w", encoding="utf-8") as f:
        f.write(json.dumps(dict_peers, ensure_ascii=False, indent=2))

def __download_peer_meta():
    peer_meta_url = f"https://raw.githubusercontent.com/710850609/EasyTier-EUI/refs/heads/main/configs/peers.json"
    test_peer_mark_file = Path(run_configs.data_dir(), 'test-peer-source')
    if test_peer_mark_file.exists():
        peer_meta_url = peer_meta_url.replace('.json', '-test.json')
    try:
        data = github_util.download_raw_file(peer_meta_url, timeout=10)
        peer_meta_file = run_configs.et_peer_meta_file()
        with open(peer_meta_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return data
    except Exception as e:
        logging.exception(f"获取节点元数据失败")
        raise HttpException(f'获取公共节点失败, 请检查网络连接或切换Github加速地址： {e}')

def __sort_peers(peers: list[dict]):
    peers.sort(key=lambda x: (-x.get('status'), x.get('latency', 0), x.get('src_uri', ''), x.get('uri', '')))
