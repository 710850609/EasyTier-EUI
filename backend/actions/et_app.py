#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from actions import et_core
from http_dispatcher.dispatcher import HttpException
from utils import validators, github_util
from utils.validators import Validator


def get_download_url(params: dict, *kwargs):
    params = params or {}
    platform, _ = Validator.not_empty(params, 'platform')
    arch, _ = Validator.not_empty(params, 'arch')
    prerelease, _ = Validator.not_empty(params, 'prerelease')
    prerelease = prerelease.lower() == 'true'

    release_info = et_core.get_release_info({})
    versions = release_info.get('versions', [])
    download_url = ''
    for version in versions:
        if version.get('prerelease') == prerelease:
            info = version
            platform_arch = f"{platform}-{arch}"
            download_url = version.get('assets', {}).get(platform_arch, {}).get('download_url')
            break
    if download_url == '':
        raise HttpException(f'未找到{platform} {arch}的下载链接')
    return github_util.get_download_url_proxy(download_url)
