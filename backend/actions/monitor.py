#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from et_adapters import get_facade
from utils.validators import Validator

logger = logging.getLogger(__name__)

def list(params, *args, **kwargs):
    """
    获取节点列表
    :param request_data: 请求数据（可选）
    """
    profile, _ = Validator.not_empty(params, 'profile', 'validate.profile_required')
    profile = Validator.check_profile(profile)
    relay_path = params.get('relay_path', 'false')
    relay_path = relay_path.lower() == 'true'
    return get_facade().get_peers(profile, relay_path)
