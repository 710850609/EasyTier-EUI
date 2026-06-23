#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from actions import et_core
from http_dispatcher.dispatcher import HttpException
from utils import github_util
from utils.validators import Validator


def get_download_url(params: dict, *args, **kwargs):
    params = params or {}
    arch, _ = Validator.not_empty(params, 'arch')
    type, _ = Validator.not_empty(params, 'type')
    prerelease, _ = Validator.not_empty(params, 'prerelease')
    prerelease = prerelease.lower() == 'true'

    release_info = et_core.get_release_info({})
    versions = release_info.get('versions', [])
    download_url = ''
    for version in versions:
        if version.get('prerelease') == prerelease:
            platform_arch = f"{arch}-{type}"
            download_url = version.get('assets', {}).get(platform_arch, {}).get('download_url')
            break
    if download_url == '':
        raise HttpException(f'未找到 {arch}-{type} 的下载链接')
    return github_util.get_download_url_proxy(download_url)
