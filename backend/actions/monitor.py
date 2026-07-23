#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import sys

from utils import common_util, et_run_info
from utils import run_configs
from utils.et_bridge import et_bridge
from utils.validators import Validator


def list(params, *args, **kwargs):
    """
    获取节点列表
    :param request_data: 请求数据（可选）
    """
    if run_configs.IS_ANDROID:
        if et_bridge is None or et_bridge._lib is None:
            return []
        try:
            return et_bridge.get_peers()
        except Exception as e:
            logging.warning(f"Android: Failed to get peers: {e}")
            return []
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    info = et_run_info.get(profile)
    if not info:
        logging.debug(f"未找到配置元数据：{profile}")
        return []
    if not info.rpc_portal:
        logging.debug(f"元数据没有rpc信息：{info.__dict__}")
        return []
    _ext = ".exe" if sys.platform == "win32" else ""
    cmd = f"{os.path.join(run_configs.core_dir(), 'easytier-cli')}{_ext} -o json  --rpc-portal {info.rpc_portal} peer"
    try:
        result = common_util.run_cmd(cmd)
        peer_list = json.loads(result)
        return peer_list
    except Exception as e:
        if str(e).find('failed to connect to server') > 0:
            logging.debug(str(e))
            return []
        raise e