#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys

from http_dispatcher.dispatcher import HttpException
from utils import common_util, et_run_info
from utils import run_configs


def list(params, *kwargs):
    """
    获取节点列表
    :param request_data: 请求数据（可选）
    """
    if params is None:
        params = {}
    profile = params.get('profile')
    info = et_run_info.get(profile)
    if not info:
        raise HttpException(f"unknown rpc profile {profile}")
    _ext = ".exe" if sys.platform == "win32" else ""
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} -o json --rpc-portal {info.rpc_portal} peer"
    result = common_util.run_cmd(cmd)
    peer_list = json.loads(result)
    return peer_list
