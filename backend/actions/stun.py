#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import platform
import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import common_util
from utils import github_util
from utils import run_configs, process_util
from utils.validators import Validator

logger = logging.getLogger(__name__)


def _get_stun_dir() -> str:
    return os.path.join(run_configs.data_dir(), 'stun')


def _get_running_dir(config_id: str) -> str:
    return os.path.join(_get_stun_dir(), 'running', config_id)


def _get_natmap_binary() -> str | None:
    # 为防止飞牛系统升级导致 natmap 不存在，存储到 data_dir
    install_dir = run_configs.data_dir()
    if sys.platform == 'win32':
        bin_path = os.path.join(install_dir, 'natmap', 'natmap.exe')
    else:
        bin_path = os.path.join(install_dir, 'natmap', 'natmap')
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

def nat_check(params=None, *args, **kwargs):
    from stun import natter_check
    nat_type = natter_check.get_nat_type()
    return nat_type

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
            shutil.move(os.path.join(tmp_dir, 'natmap'), run_configs.data_dir())
        else:
            natmap_dir = os.path.join(run_configs.data_dir(), 'natmap')
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
            if 'mapping' not in config or 'dns_record' not in config.get('mapping', {}):
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
    exists_id = params.get('id')
    config_id = params.get('id') or uuid.uuid4().hex[:8]
    config['id'] = config_id

    sc = config.get('stunConfig', {})
    listen_protocol = sc.get('listenProtocol', '')
    protocol = {
        'tcp': 'tcp',
        'udp': 'udp',
        'wg': 'udp',
        'ws': 'tcp',
        'wss': 'tcp',
        'quic': 'udp',
        'faketcp': 'udp',
    }.get(listen_protocol, '')
    listen_port = str(sc.get('listenPort', ''))
    if not listen_port:
        raise HttpException(get_message('stun.listenPortRequired'))
    bind_port = str(sc.get('bindPort', ''))
    sc['protocol'] = protocol

    stun_configs = _load_stun()
    for existing_id, existing_config in stun_configs.items():
        if existing_id == config_id:
            continue
        esc = existing_config.get('stunConfig', {})
        if str(esc.get('listenPort', '')) == listen_port and esc.get('protocol', '') == protocol:
            raise HttpException(get_message('stun.duplicateProtocolBindPort'))
        if bind_port and bind_port != '0' and (
                bind_port == listen_port
                or str(esc.get('bindPort', '')) == bind_port
                or str(esc.get('listenPort', '')) == bind_port
        ):
            raise HttpException(get_message('stun.duplicateBindPort'))

    config.pop('running', None)
    config.pop('mapping', None)
    config.pop('error_msg', None)
    stun_configs[config_id] = config
    if exists_id:
        stop_stun({'id': config_id})
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


def _build_callback_script(config: dict) -> str:
    config_id = config.get('id', '')
    running_dir = _get_running_dir(config_id)
    os.makedirs(running_dir, exist_ok=True)
    mapping_file = os.path.join(running_dir, 'mapping.json')
    error_file = os.path.join(running_dir, 'error.txt')
    callback_log = os.path.join(run_configs.log_dir(), 'stun', f'stun-{config_id}.log')
    os.makedirs(os.path.dirname(callback_log), exist_ok=True)
    listen_protocol = config.get('stunConfig', {}).get('listenProtocol', '')
    if not listen_protocol:
        raise HttpException(get_message('stun.listenProtocolRequired'))

    # 根据 DNS 服务商构建回调参数（后续扩展在此添加 elif 分支）
    changeConfig = config.get('changeConfig', {})
    dns_provider = changeConfig.get('dnsProvider', '')
    callback_script_params = {}
    dns_script_src = None

    if dns_provider == 'dynv6':
        domain = changeConfig.get('domain', '')
        http_token = changeConfig.get('httpToken', '')
        if domain and http_token:
            domain_parts = domain.split('.')
            zone = '.'.join(domain_parts[-3:])
            record_name = domain.removesuffix(f'{zone}').removesuffix('.')
            if zone:
                dns_script_name = f'update_dns_dynv6.{"bat" if sys.platform == "win32" else "sh"}'
                assets_dir = run_configs.dns_callback_script_path()
                dns_script_src = os.path.join(assets_dir, dns_script_name)
                callback_script_params = {
                    'zone': zone,
                    'record_name': record_name,
                    'http_token': http_token,
                }

    dns_callback_script = None
    if dns_script_src:
        dns_callback_script = os.path.join(_get_stun_dir(), os.path.basename(dns_script_src))
        shutil.copy2(dns_script_src, dns_callback_script)
        # 确保 Windows bat 文件带 BOM，否则 chcp 65001 + 中文会出现乱码
        if sys.platform == 'win32' and dns_callback_script.endswith('.bat'):
            with open(dns_callback_script, 'rb') as f:
                raw = f.read()
            if not raw.startswith(b'\xef\xbb\xbf'):
                with open(dns_callback_script, 'wb') as f:
                    f.write(b'\xef\xbb\xbf' + raw)
        if sys.platform != 'win32':
            os.chmod(dns_callback_script, 0o755)

    if sys.platform == 'win32':
        script_path = os.path.join(running_dir, 'callback.bat')
        mapping_json = '{"public_addr":"%1","public_port":"%2","ip4p":"%3","private_port":"%4","protocol":"%5","private_addr":"%6"}'
        script_content = (
            f'@echo off\r\n'
            f'chcp 65001 >nul\r\n'
            f'setlocal enabledelayedexpansion\r\n'
            f'for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "(Get-Date).ToString(\'yyyy-MM-dd HH:mm:ss\')"`) do set "TS=%%I"\r\n'
            f'set CHANGED=1\r\n'
            f'if exist "{mapping_file}" (\r\n'
            f'    powershell -NoProfile -Command "$j = Get-Content \'{mapping_file}\' -Raw | ConvertFrom-Json; if ($j.public_addr -eq \'%1\' -and $j.public_port -eq \'%2\') {{ exit 1 }} else {{ exit 0 }}"\r\n'
            f'    if errorlevel 1 set CHANGED=0\r\n'
            f')\r\n'
            f'>> "{callback_log}" 2>&1 echo !TS! [natmap-callback] started: public_addr=%1 public_port=%2 ip4p=%3 private_port=%4 protocol=%5 private_addr=%6\r\n'
        )
        if dns_callback_script:
            callback_cmd = f'"{dns_callback_script}" -protocol "{listen_protocol}" -ip "%1" -port "%2"'
            for key, value in callback_script_params.items():
                callback_cmd += f' -{key} "{value}"'
            script_content += (
                f'if !CHANGED!==1 (\r\n'
                f'    echo {mapping_json}> "{mapping_file}"\r\n'
                f'    >> "{callback_log}" 2>&1 echo !TS! [natmap-callback] triggering DNS update...\r\n'
                f'    if exist "{dns_callback_script}" (\r\n'
                f'        set "DNS_RESULT_FILE=%TEMP%\\dns_result_!RANDOM!.txt"\r\n'
f'        call {callback_cmd} > "!DNS_RESULT_FILE!" 2>> "{callback_log}"\r\n'
                f'        set DNS_RC=!ERRORLEVEL!\r\n'
                f'        >> "{callback_log}" 2>&1 echo !TS! [natmap-callback] DNS update exit code=!DNS_RC!\r\n'
                f'        if !DNS_RC!==0 (\r\n'
                f'            if exist "!DNS_RESULT_FILE!" (\r\n'
                f'                set /p DNS_RECORD=<"!DNS_RESULT_FILE!"\r\n'
                f'                powershell -NoProfile -Command "$j=Get-Content \'{mapping_file}\' -Raw|ConvertFrom-Json; $j|Add-Member -NotePropertyValue \\"!DNS_RECORD!\\" -NotePropertyName \'dns_record\'; $j|ConvertTo-Json -Compress|Set-Content \'{mapping_file}\'"\r\n'
                f'                >> "{callback_log}" 2>&1 echo !TS! [natmap-callback] DNS record updated: !DNS_RECORD!\r\n'
                f'            )\r\n'
                f'        ) else (\r\n'
                f'            >> "{error_file}" echo !TS! [natmap-callback] DNS update failed with exit code !DNS_RC!\r\n'
                f'        )\r\n'
                f'        del "!DNS_RESULT_FILE!" 2>nul\r\n'
                f'    ) else (\r\n'
                f'        >> "{callback_log}" 2>&1 echo !TS! [natmap-callback] DNS script not found: {dns_callback_script}\r\n'
                f'    )\r\n'
                f') else (\r\n'
                f'    >> "{callback_log}" 2>&1 echo !TS! [natmap-callback] public addr/port unchanged, skipping DNS update\r\n'
                f')\r\n'
            )
        else:
            script_content += f'echo {mapping_json}> "{mapping_file}"\r\n'
            script_content += f'>> "{callback_log}" 2>&1 echo !TS! [natmap-callback] DNS update skipped (no zone/token configured)\r\n'
        script_content += (
            f'>> "{callback_log}" 2>&1 echo !TS! [natmap-callback] completed\r\n'
            f'powershell -NoProfile -Command "Get-Content \'{callback_log}\' | Select-Object -Last 1000 | Set-Content \'{callback_log}\'"\r\n'
        )
    else:
        script_path = os.path.join(running_dir, 'callback.sh')
        script_content = (
            '#!/bin/sh\n'
            f'ts() {{ date \'+%Y-%m-%d %H:%M:%S\'; }}\n'
            f'>> "{callback_log}" echo "$(ts) [natmap-callback] started: public_addr=$1 public_port=$2 ip4p=$3 private_port=$4 protocol=$5 private_addr=$6"\n'
            f'CHANGED=1\n'
            f'if [ -f "{mapping_file}" ]; then\n'
            f'    OLD_ADDR=$(sed -n \'s/.*"public_addr":"\\([^"]*\\)".*/\\1/p\' "{mapping_file}")\n'
            f'    OLD_PORT=$(sed -n \'s/.*"public_port":"\\([^"]*\\)".*/\\1/p\' "{mapping_file}")\n'
            f'    if [ "$OLD_ADDR" = "$1" ] && [ "$OLD_PORT" = "$2" ]; then\n'
            f'        CHANGED=0\n'
            f'    fi\n'
            f'fi\n'
        )
        if dns_callback_script:
            callback_cmd = f'"{dns_callback_script}" -protocol "{listen_protocol}" -ip "$1" -port "$2"'
            for key, value in callback_script_params.items():
                callback_cmd += f' -{key} "{value}"'
            script_content += (
                f'if [ $CHANGED -eq 1 ]; then\n'
                f'    echo \'{{"public_addr":"\'$1\'","public_port":"\'$2\'","ip4p":"\'$3\'","private_port":"\'$4\'","protocol":"\'$5\'","private_addr":"\'$6\'"}}\' > "{mapping_file}"\n'
                f'    >> "{callback_log}" echo "$(ts) [natmap-callback] triggering DNS update..."\n'
                f'    if [ -f "{dns_callback_script}" ]; then\n'
                f'        DNS_RECORD=$({callback_cmd} 2>> "{callback_log}")\n'
                f'        RC=$?\n'
                f'        >> "{callback_log}" echo "$(ts) [natmap-callback] DNS update exit code=$RC"\n'
                f'        if [ $RC -eq 0 ]; then\n'
                f'            if [ -n "$DNS_RECORD" ]; then\n'
                f'                sed -i "s|}}$|,\\"dns_record\\":\\"${{DNS_RECORD}}\\"}}|" "{mapping_file}"\n'
                f'                >> "{callback_log}" echo "$(ts) [natmap-callback] DNS record updated: $DNS_RECORD"\n'
                f'            fi\n'
                f'        else\n'
                f'            echo "$(ts) [natmap-callback] DNS update failed with exit code $RC" >> "{error_file}"\n'
                f'        fi\n'
                f'    else\n'
                f'        >> "{callback_log}" echo "$(ts) [natmap-callback] DNS script not found: {dns_callback_script}"\n'
                f'    fi\n'
                f'else\n'
                f'    >> "{callback_log}" echo "$(ts) [natmap-callback] public addr/port unchanged, skipping DNS update"\n'
                f'fi\n'
            )
        else:
            script_content += f'echo \'{{"public_addr":"\'$1\'","public_port":"\'$2\'","ip4p":"\'$3\'","private_port":"\'$4\'","protocol":"\'$5\'","private_addr":"\'$6\'"}}\' > "{mapping_file}"\n'
            script_content += f'>> "{callback_log}" echo "$(ts) [natmap-callback] DNS update skipped (no zone/token configured)"\n'
        script_content += (
            f'>> "{callback_log}" echo "$(ts) [natmap-callback] completed"\n'
            f'tail -n 1000 "{callback_log}" > "{callback_log}.tmp" && mv "{callback_log}.tmp" "{callback_log}"\n'
        )

    encoding = 'utf-8-sig' if sys.platform == 'win32' else 'utf-8'
    with open(script_path, 'w', encoding=encoding) as f:
        f.write(script_content)
    if sys.platform != 'win32':
        os.chmod(script_path, 0o755)
    logger.info(f'生成 natmap 回调脚本: {script_path}')
    return script_path


def _build_launcher_script(config_id: str, natmap_cmd: list[str]) -> str:
    running_dir = _get_running_dir(config_id)
    os.makedirs(running_dir, exist_ok=True)
    error_file = os.path.join(running_dir, 'error.txt')
    mapping_file = os.path.join(running_dir, 'mapping.json')
    app_log = os.path.join(run_configs.log_dir(), 'stun', f'stun-{config_id}.log')
    os.makedirs(os.path.dirname(app_log), exist_ok=True)
    natmap_cmd_str = ' '.join(f'"{x}"' if ' ' in x else x for x in natmap_cmd)

    interval = 60
    if sys.platform == 'win32':
        # 在 Windows 上，无论加不加 -e，hev_stun_run 这一次任务内部都只做一次 STUN 绑定就退出（break），不会在同一个任务里反复轮询
        script_path = os.path.join(running_dir, 'launcher.bat')
        script_content = (
            '@echo off\r\n'
            'chcp 65001 >nul\r\n'
            f'set "EF={error_file}"\r\n'
            ':loop\r\n'
            f'{natmap_cmd_str} 2>&1 1>NUL | powershell -NoProfile -Command "$ring=@(); $ef=$env:EF; while(($line=[Console]::In.ReadLine()) -ne $null){{ $ts=Get-Date -Format \'yyyy-MM-dd HH:mm:ss\'; $ring+=($ts+\' \'+$line); if($ring.Count -gt 4){{$ring=$ring[-4..-1]}}; $utf8=[System.Text.UTF8Encoding]::new($false); [IO.File]::WriteAllLines($ef, $ring, $utf8) }}"\r\n'
            f'ping -n {interval + 1} 127.0.0.1 >nul\r\n'
            'goto loop\r\n'
        )
    else:
        script_path = os.path.join(running_dir, 'launcher.sh')
        script_content = (
            '#!/bin/sh\n'
            f'> "{error_file}"\n'
            f'{natmap_cmd_str} 2>&1 >/dev/null | while IFS= read -r line; do\n'
            f'    rm -f "{mapping_file}"\n'
            f'    echo "$(date \'+%Y-%m-%d %H:%M:%S\') $line" >> "{error_file}"\n'
            f'    tail -n 4 "{error_file}" > "{error_file}.tmp" && mv "{error_file}.tmp" "{error_file}"\n'
            f'done\n'
        )

    encoding = 'utf-8-sig' if sys.platform == 'win32' else 'utf-8'
    with open(script_path, 'w', encoding=encoding) as f:
        f.write(script_content)
    if sys.platform != 'win32':
        os.chmod(script_path, 0o755)
    logger.info(f'生成 natmap 启动器脚本: {script_path}')
    return script_path


def start_stun(params=None, *args, **kwargs):
    params = params or {}
    config_id, _ = Validator.not_empty(params, 'id', 'stun.idRequired')
    stun_configs = _load_stun()
    config = stun_configs.get(config_id) or {}
    if not config:
        raise HttpException(get_message('stun.configNotFound'))
    stun_config = config.get("stunConfig") or {}
    listen_port = stun_config.get('listenPort')
    if not listen_port:
        raise HttpException(get_message('stun.listenPortRequired'))
    default_http_server = "www.baidu.com"
    default_stun_server = "turn.cloud-rtc.com:80"
    is_udp_mode = stun_config.get('protocol', '').lower() == 'udp'
    natmap_binary = _get_natmap_binary()
    if natmap_binary is None:
        raise HttpException(get_message('stun.natmapBinaryNotFound'))
    cmd_list = [natmap_binary, '-4']
    if is_udp_mode:
        cmd_list.append('-u')
        default_http_server = "119.29.29.29"
        default_stun_server = "stun.miwifi.com"
    if stun_config.get('bindPort'):
        # 指定了 bindPort，则走转发模式
        cmd_list.append('-t')
        cmd_list.append("127.0.0.1")
        cmd_list.append('-p')
        cmd_list.append(listen_port)
        cmd_list.append('-b')
        cmd_list.append(stun_config.get('bindPort'))
    else:
        # 没指定 bindPort，则绑定 listenPort
        cmd_list.append('-b')
        cmd_list.append(listen_port)

    if stun_config.get('interface'):
        cmd_list.append('-i')
        cmd_list.append(stun_config.get('interface'))
    if stun_config.get('checkCycle'):
        cmd_list.append('-c')
        cmd_list.append(stun_config.get('checkCycle'))

    cmd_list.append('-k')
    cmd_list.append(stun_config.get('keepaliveInterval') or "25")
    if is_udp_mode:
        cmd_list.append('-c')
        cmd_list.append(stun_config.get('keepaliveInterval') or "2")

    cmd_list.append('-s')
    cmd_list.append(stun_config.get('stunServer') or default_stun_server)
    if not is_udp_mode:
        cmd_list.append('-h')
        cmd_list.append(stun_config.get('httpServer') or default_http_server)

    running_dir = _get_running_dir(config_id)
    _cleanup_running_dir(config_id)
    os.makedirs(running_dir, exist_ok=True)

    config['status'] = 1
    _save_stun_configs(stun_configs)

    pid_file = os.path.join(running_dir, 'pid.txt')
    pm = process_util.ProcessManager(pid_file)

    callback_script = _build_callback_script(config)
    cmd_list.extend(['-e', callback_script])

    if sys.platform == 'win32':
        launcher_script = _build_launcher_script(config_id, cmd_list)
        logger.info(f"stun 启动器: {launcher_script}")
        pm.start(['cmd.exe', '/c', launcher_script])
    else:
        launcher_script = _build_launcher_script(config_id, cmd_list)
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
    config['status'] = 0
    _save_stun_configs(stun_configs)

def start_enable(params=None, *args, **kwargs):
    try:
        stun_configs = list_stun()
        for config in stun_configs:
            if str(config.get('status', 0)) == '1' and not config.get('running'):
                logger.info(f"开启 stun 配置: {config}")
                start_stun({'id': config.get('id')})
    except Exception as e:
        logger.error(f"开启 stun 配置失败: {e}")
        pass


def stop_all(params=None, *args, **kwargs):
    stun_configs = _load_stun()
    for config_id, config in stun_configs.items():
        if str(config.get('status', 0)) == '1':
            logger.info(f"停止 stun 配置: {config}")
            stop_stun({'id': config_id})