#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import json
import logging
import os
import platform
import re
import shutil
import sys
import time
import uuid
import zipfile
from ipaddress import ip_address
from pathlib import Path

from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import run_configs, process_util, ip_util
from utils import github_util
from utils import common_util
from utils.validators import Validator

logger = logging.getLogger(__name__)


def _get_stun_dir() -> str:
    return os.path.join(run_configs.data_dir(), 'stun')


def _get_running_dir(config_id: str) -> str:
    return os.path.join(_get_stun_dir(), 'running', config_id)


def _get_natmap_binary() -> str | None:
    core_dir = run_configs.core_dir()
    if sys.platform == 'win32':
        bin_path = os.path.join(core_dir, 'natmap', 'natmap.exe')
    else:
        bin_path = os.path.join(core_dir, 'natmap', 'natmap')
    if os.path.exists(bin_path):
        return bin_path
    return None


def _get_natmap_version(bin_path: str) -> str | None:
    try:
        return_code, stdout, stderr = common_util.run_cmd(bin_path, check_result=False)
        last_line = stderr.strip().split('\n')[-1].strip()
        match = re.search(r'Version:\s*(\S+)', last_line)
        if match:
            return match.group(1)
    except Exception as e:
        logger.warning(f'获取 natmap 版本失败: {e}')
        return None


def natmap_version(params=None, *args, **kwargs):
    bin_path = _get_natmap_binary()
    exists_natmap = bin_path is not None
    current_version = _get_natmap_version(bin_path) if bin_path else None
    return {
        'exists_natmap': exists_natmap,
        'current_version': current_version
    }


def natmap_install(params=None, *args, **kwargs):
    system = sys.platform
    if system == 'win32':
        platform_name = 'win64'
    elif system == 'darwin':
        platform_name = 'darwin'
    else:
        platform_name = 'linux'

    machine = platform.machine().lower()
    arch_map = {
        'x86_64': 'x86_64',
        'arm64': 'arm64',
        'armv7l': 'arm32',
    }
    arch = arch_map.get(machine, machine)
    arch_name = '.zip' if platform_name == 'win64' else f'-{arch}'
    filename = f'natmap-{platform_name}{arch_name}'
    download_url = f'https://github.com/heiher/natmap/releases/latest/download/{filename}'

    try:
        logger.info(f'下载 natmap: {download_url}')
        core_dir = run_configs.core_dir()
        os.makedirs(core_dir, exist_ok=True)

        tmp_dir = os.path.join(run_configs.data_dir(), 'download', 'natmap')
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir, exist_ok=True)

        download_path = os.path.join(tmp_dir, filename)
        github_util.download_release_file(download_url, download_path, desc=filename)

        if filename.endswith('.zip'):
            logger.info(f'解压 natmap: {download_path}')
            with zipfile.ZipFile(download_path, 'r') as zf:
                zf.extractall(tmp_dir)
            shutil.move(os.path.join(tmp_dir, 'natmap'), run_configs.core_dir())
        else:
            natmap_dir = os.path.join(run_configs.core_dir(), 'natmap')
            Path(natmap_dir).mkdir(parents=True, exist_ok=True)
            shutil.move(download_path, os.path.join(natmap_dir, 'natmap'))

        target_path = _get_natmap_binary()
        if not target_path:
            raise HttpException(get_message('stun.natmapBinaryNotFound'))

        if sys.platform != 'win32':
            os.chmod(target_path, 0o755)

        shutil.rmtree(tmp_dir, ignore_errors=True)

        version = _get_natmap_version(target_path)
        logger.info(f'natmap 安装成功，版本: {version}')
        return {'success': True, 'version': version}
    except HttpException:
        raise
    except Exception as e:
        logger.error(f'natmap 安装失败: {e}')
        raise HttpException(get_message('stun.natmapInstallFailed', error=str(e)))

def _load_stun():
    stun_file = os.path.join(_get_stun_dir(), 'stun.json')
    if os.path.exists(stun_file):
        with open(stun_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = {}
        for name, config in data.items():
            result[name] = json.loads(config) if isinstance(config, str) else config
        return result
    return {}

def _save_stun_configs(stun_configs: dict):
    stun_dir = _get_stun_dir()
    os.makedirs(stun_dir, exist_ok=True)
    stun_file = os.path.join(stun_dir, 'stun.json')
    with open(stun_file, "w", encoding="utf-8") as f:
        json.dump(stun_configs, f, ensure_ascii=False, indent=4)

def list_stun(params=None, *args, **kwargs):
    stun_configs = _load_stun()
    stun_list = []
    for config_id, config in stun_configs.items():
        running_dir = _get_running_dir(config_id)
        pid_file = os.path.join(running_dir, 'pid.txt')
        pm = process_util.ProcessManager(pid_file)
        running = pm.status()
        config['running'] = running
        if running:
            mapping_file = os.path.join(running_dir, 'mapping.json')
            if os.path.exists(mapping_file):
                try:
                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        config['mapping'] = json.load(f)
                except Exception:
                    pass
            else:
                error_file = os.path.join(running_dir, 'error.txt')
                if os.path.exists(error_file):
                    try:
                        with open(error_file, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read().strip()
                        if content:
                            config['error_msg'] = content
                    except Exception:
                        pass
        stun_list.append(config)
    return stun_list

def save_stun(params=None, *args, **kwargs):
    params = params or {}
    config, _ = Validator.not_empty(params, 'config', 'stun.configRequired')
    config_id = params.get('id') or uuid.uuid4().hex[:8]
    config['id'] = config_id

    sc = config.get('stunConfig', {})
    protocol = sc.get('protocol', '')
    bind_port = str(sc.get('bindPort', ''))

    stun_configs = _load_stun()
    for existing_id, existing_config in stun_configs.items():
        if existing_id == config_id:
            continue
        esc = existing_config.get('stunConfig', {})
        if str(esc.get('bindPort', '')) == bind_port and esc.get('protocol', '') == protocol:
            raise HttpException(get_message('stun.duplicateProtocolBindPort'))

    config.pop('running', None)
    config.pop('mapping', None)
    config.pop('error_msg', None)
    stun_configs[config_id] = config
    _save_stun_configs(stun_configs)
    return {'id': config_id}

def delete_stun(params=None, *args, **kwargs):
    params = params or {}
    config_id, _ = Validator.not_empty(params, 'id', 'stun.idRequired')
    stun_configs = _load_stun()
    if config_id not in stun_configs:
        raise HttpException(get_message('stun.configNotFound'))
    del stun_configs[config_id]
    _save_stun_configs(stun_configs)
    _cleanup_running_dir(config_id)
    return {'success': True}

def _cleanup_running_dir(config_id: str):
    running_dir = _get_running_dir(config_id)
    if os.path.exists(running_dir):
        shutil.rmtree(running_dir, ignore_errors=True)
        logger.info(f'清理运行目录: {running_dir}')


def _build_callback_script(config_id: str):
    running_dir = _get_running_dir(config_id)
    os.makedirs(running_dir, exist_ok=True)
    mapping_file = os.path.join(running_dir, 'mapping.json')
    dns_script = os.path.join(_get_stun_dir(), 'dns', 'dyv6.sh')
    dns_script_bat = dns_script.replace('/', '\\')

    if sys.platform == 'win32':
        script_path = os.path.join(running_dir, 'callback.bat')
        script_content = (
            '@echo off\r\n'
            'for /f "delims=" %%t in (\'powershell -NoProfile -Command "Get-Date -Format \'yyyy-MM-dd HH:mm:ss\'"\') do set "TS=%%t"\r\n'
            f'echo {{"public_addr":"%1","public_port":"%2","ip4p":"%3","private_port":"%4","protocol":"%5","private_addr":"%6","update_time":"%TS%"}}> "{mapping_file}"\r\n'
            f'if exist "{dns_script_bat}" call "{dns_script_bat}" {config_id} "%1" "%2" "%3" "%4" "%5" "%6"\r\n'
        )
    else:
        script_path = os.path.join(running_dir, 'callback.sh')
        script_content = (
            '#!/bin/sh\n'
            f'echo \'{{"public_addr":"\'$1\'","public_port":"\'$2\'","ip4p":"\'$3\'","private_port":"\'$4\'","protocol":"\'$5\'","private_addr":"\'$6\'","update_time":"\'$(date \'+%Y-%m-%d %H:%M:%S\')\'"}}\' > "{mapping_file}"\n'
            f'if [ -f "{dns_script}" ]; then\n'
            f'    sh "{dns_script}" {config_id} "$1" "$2" "$3" "$4" "$5" "$6"\n'
            f'fi\n'
        )
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        return script_path

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    logger.info(f'生成 natmap 回调脚本: {script_path}')
    return script_path


def _build_launcher_script(config_id: str, natmap_cmd: list[str]) -> tuple[str, str]:
    running_dir = _get_running_dir(config_id)
    os.makedirs(running_dir, exist_ok=True)
    error_file = os.path.join(running_dir, 'error.txt')
    mapping_file = os.path.join(running_dir, 'mapping.json')
    natmap_cmd_str = ' '.join(f'"{x}"' if ' ' in x else x for x in natmap_cmd)

    interval = 3
    if sys.platform == 'win32':
        script_path = os.path.join(running_dir, 'launcher.bat')
        script_content = (
            '@echo off\r\n'
            'chcp 65001 >nul\r\n'
            f'set "EF={error_file}"\r\n'
            ':loop\r\n'
            f'{natmap_cmd_str} 2>&1 | powershell -NoProfile -Command "$ring=@(); $ef=$env:EF; while(($line=[Console]::In.ReadLine()) -ne $null){{ $ts=Get-Date -Format \'yyyy-MM-dd HH:mm:ss\'; $ring+=($ts+\' \'+$line); if($ring.Count -gt 4){{$ring=$ring[-4..-1]}}; $utf8=[System.Text.UTF8Encoding]::new($false); [IO.File]::WriteAllLines($ef, $ring, $utf8) }}"\r\n'
            f'ping -n {interval + 1} 127.0.0.1 >nul\r\n'
            'goto loop\r\n'
        )
    else:
        script_path = os.path.join(running_dir, 'launcher.sh')
        script_content = (
            '#!/bin/sh\n'
            'while true; do\n'
            f'    > "{error_file}"\n'
            f'    {natmap_cmd_str} 2>&1 | while IFS= read -r line; do\n'
            f'        rm -f "{mapping_file}"\n'
            f'        echo "$(date \'+%Y-%m-%d %H:%M:%S\') $line" >> "{error_file}"\n'
            f'        tail -n 4 "{error_file}" > "{error_file}.tmp" && mv "{error_file}.tmp" "{error_file}"\n'
            f'    done\n'
            f'    sleep {interval}\n'
            f'done\n'
        )
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        logger.info(f'生成 natmap 启动器脚本: {script_path}')
        return script_path, script_content

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    logger.info(f'生成 natmap 启动器脚本: {script_path}')
    return script_path, script_content


def start_stun(params=None, *args, **kwargs):
    params = params or {}
    config_id, _ = Validator.not_empty(params, 'id', 'stun.idRequired')
    stun_configs = _load_stun()
    config = stun_configs.get(config_id) or {}
    if not config:
        raise HttpException(get_message('stun.configNotFound'))
    stun_config = config.get("stunConfig") or {}
    cmd_list = [_get_natmap_binary()]
    default_http_server = "www.baidu.com"
    default_stun_server = "turn.cloud-rtc.com:80"
    is_udp_mode = stun_config.get('protocol', '').lower() == 'udp'
    if is_udp_mode:
        cmd_list.append('-u')
        default_http_server = "119.29.29.29"
        default_stun_server = "stun.miwifi.com"
    if stun_config.get('bindPort'):
        if sys.platform == 'win32':
            # cmd_list.append('-t')
            # cmd_list.append("127.0.0.1")
            # cmd_list.append('-p')
            # cmd_list.append(stun_config.get('bindPort'))
            # cmd_list.append("20000-30000")
            cmd_list.append('-b')
            cmd_list.append(stun_config.get('bindPort'))
        else:
            cmd_list.append('-b')
            cmd_list.append(stun_config.get('bindPort'))
    if stun_config.get('interface'):
        cmd_list.append('-i')
        cmd_list.append(stun_config.get('interface'))
    if stun_config.get('checkCycle'):
        cmd_list.append('-c')
        cmd_list.append(stun_config.get('checkCycle'))

    cmd_list.append('-k')
    cmd_list.append(stun_config.get('keepaliveInterval') or "5")
    if is_udp_mode:
        cmd_list.append('-c')
        cmd_list.append(stun_config.get('keepaliveInterval') or "1")

    cmd_list.append('-s')
    cmd_list.append(stun_config.get('stunServer') or default_stun_server)
    if not is_udp_mode:
        cmd_list.append('-h')
        cmd_list.append(stun_config.get('httpServer') or default_http_server)

    running_dir = _get_running_dir(config_id)
    _cleanup_running_dir(config_id)
    os.makedirs(running_dir, exist_ok=True)

    pid_file = os.path.join(running_dir, 'pid.txt')
    pm = process_util.ProcessManager(pid_file)

    callback_script = _build_callback_script(config_id)
    cmd_list.extend(['-e', callback_script])

    if sys.platform == 'win32':
        launcher_script, _ = _build_launcher_script(config_id, cmd_list)
        logger.info(f"stun 启动器: {launcher_script}")
        pm.start(['cmd.exe', '/c', launcher_script])
    else:
        launcher_script, _ = _build_launcher_script(config_id, cmd_list)
        logger.info(f"stun 启动器: {launcher_script}")
        pm.start(['sh', launcher_script])


def stop_stun(params=None, *args, **kwargs):
    params = params or {}
    config_id, _ = Validator.not_empty(params, 'id', 'stun.idRequired')
    stun_configs = _load_stun()
    config = stun_configs.get(config_id) or {}
    if not config:
        raise HttpException(get_message('stun.configNotFound'))
    running_dir = _get_running_dir(config_id)
    pid_file = os.path.join(running_dir, 'pid.txt')
    pm = process_util.ProcessManager(pid_file)
    pm.stop(timeout=0)
    _cleanup_running_dir(config_id)