#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from actions import et_core
from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import github_util
from utils.validators import Validator

def get_app_info(params: dict, *args, **kwargs):
    release_info = et_core.get_release_info({'refresh': 'true'})
    app_info = {'release': {'version': ''}, 'prerelease': {'version': ''}}
    versions = release_info.get('versions', [])
    get_release = False
    get_prerelease = False
    for version in versions:
        if get_prerelease and get_release:
            break
        if not version.get('prerelease') and not get_release:
            app_info['release']['version'] = version.get('version')
            get_release = True
            continue
        if version.get('prerelease') and not get_prerelease:
            app_info['prerelease']['version'] = version.get('version')
            get_prerelease = True
            continue
    return app_info

def get_download_url(params: dict, *args, **kwargs):
    params = params or {}
    arch, _ = Validator.not_empty(params, 'arch', 'validate.arch_required')
    type, _ = Validator.not_empty(params, 'type', 'validate.type_required')
    prerelease, _ = Validator.not_empty(params, 'prerelease', 'validate.prerelease_required')
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
        raise HttpException(get_message('download.platform_arch_not_found', arch=arch, type=type))
    return github_util.get_download_url_proxy(download_url)