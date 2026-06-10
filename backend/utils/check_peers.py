#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyTier 节点检测工具
使用 easytier-core 和 easytier-cli 检测节点连通性和延迟
"""

import json
import logging
import os
import random
import signal
import socket
import string
import subprocess
import sys
import time

from actions import peers
from utils import run_configs, log_util


def get_random_string(length=16):
    """获取随机字符串（指定长度）"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_available_port(start_port=15888, end_port=65535):
    """获取可用端口(选定范围)"""
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.bind(('0.0.0.0', port))
                if sys.platform == "win32":
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                        s2.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"在范围 {start_port}-{end_port} 内找不到可用端口")


def check_peers(bin_path, peer_list, max_wait_second = 10):
    """检测节点(节点list)"""
    core_path = os.path.join(bin_path, 'easytier-core.exe' if sys.platform == 'win32' else 'easytier-core')
    rpc_port = get_available_port(16888, 65535)
    random_string = get_random_string(16)
    
    # 构建命令
    cmd = [
        core_path,
        '--console-log-level', 'ERROR',
        '--no-listener',
        '--private-mode', 'true',
        '--rpc-portal', f"{rpc_port}",
        '--network-name', random_string,
        '--network-secret', random_string
    ]
    
    # 添加所有节点
    for peer in peer_list:
        cmd.extend(['-p', peer])
    
    logging.info(f"启动检测进程，RPC端口: {rpc_port}")
    # logging.info(f"检测节点: {peer_list}")
    
    # 启动进程
    # logging.info(f"启动检测进程: {' '.join(cmd)}")
    
    def start_process():
        if sys.platform == 'win32':
            # Windows: 使用 CREATE_NEW_PROCESS_GROUP 来允许终止进程树
            return subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
            )
        else:
            return subprocess.Popen(
                cmd,
                # stdout=subprocess.PIPE,
                # stderr=subprocess.STDOUT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding='utf-8',
                errors='ignore',
            )
    
    # 启动进程
    process = start_process()
    
    # 检查进程是否成功启动
    time.sleep(0.5)
    if process.poll() is not None:
        logging.info(f"进程启动失败，返回码: {process.returncode}")
        return {'success': {}, 'fail': peer_list}
    
    logging.info(f"检测进程启动成功，PID: {process.pid}")
    
    # 等待 RPC 服务就绪
    logging.info(f"等待 RPC 服务就绪 (127.0.0.1:{rpc_port})...")
    rpc_ready = False
    rpc_check_start = time.time()
    rpc_check_timeout = 10  # 最多等待10秒
    while (time.time() - rpc_check_start) < rpc_check_timeout:
        if process.poll() is not None:
            logging.info(f"进程已退出，返回码: {process.returncode}")
            return {'success': [], 'fail': peer_list}
        
        # 尝试连接 RPC 端口
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', rpc_port))
            sock.close()
            if result == 0:
                rpc_ready = True
                logging.info(f"RPC 服务已就绪")
                break
        except:
            pass
        time.sleep(0.5)
    

    start_check_time = time.time()
    result = None
    
    try:
        if not rpc_ready:
            raise Exception(f"EasyTier 服务未在 {rpc_check_timeout} 秒内就绪")
        while (time.time() - start_check_time) < max_wait_second:
            # 检查进程是否还在运行
            if process.poll() is not None:
                raise Exception(f"EasyTier 服务已退出，返回码: {process.returncode}")
            
            time.sleep(3)
            result = check_peers_available_use_peer(bin_path, rpc_port, peer_list)
            logging.debug(f"节点检测结果: {result}")
            # fail_list = result['fail']
            # result['fail'] = fail_list if len(result['fail']) == 0 and len(result['success']) == 0 else peer_list
            if len(result['fail']) == 0:
                break
            # logging.info(f"继续等待未连接节点: {result['fail']}")
            logging.info(f"继续检测未连接节点")

        # 排序处理
        
        return result
    finally:
        # 关闭进程
        try:
            if sys.platform == 'win32':
                os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            else:
                process.terminate()
            process.wait(timeout=2)
        except:
            try:
                process.kill()
            except:
                pass


def check_peers_available_use_peer(bin_path, rpc_port, peer_list:list):
    """检测节点可用(bin_path, rpc端口)"""
    cli_path = os.path.join(bin_path, 'easytier-cli.exe' if sys.platform == 'win32' else 'easytier-cli')
    
    cmd = [
        cli_path,
        '-v',
        '-p', f'127.0.0.1:{rpc_port}',
        '-o', 'json',
        'peer'
    ]
    
    try:
        # logging.info(f"执行检测命令: {' '.join(cmd)}")
        logging.info(f"执行节点连接检测")
        
        # 使用 Popen 替代 run，兼容 Windows Python 3.7
        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'ignore',
        }
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        process = subprocess.Popen(cmd, **kwargs)
        
        # 手动实现超时控制
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            logging.info("检测命令超时")
            process.kill()
            process.wait()
            return {'success': [], 'fail': []}
        
        if process.returncode != 0:
            logging.info(f"检测命令执行失败: {stderr}")
            return {'success': [], 'fail': []}
        
        data = json.loads(stdout)
        
        # 失败节点
        fail_peers = list(peer_list)
        # 成功节点
        success_peers = {}
        
        for item in data:
            route = item.get('route', {})
            hostname = route.get('hostname', '').replace('PublicServer_', '')
            result = {
                'relay': route.get('feature_flag', {}).get('avoid_relay_data', True) == False,
                'hostname': hostname,
            }
            conns = item.get('peer', {}).get('conns', [])
            # 支持转发
            if len(conns) > 0:
                uri = conns[0].get('tunnel', {}).get('remote_addr', {}).get('url')
                result['uri'] = uri
                # result['resolved_uri'] = conns[0].get('tunnel', {}).get('resolved_remote_addr', {}).get('url')
                latency_us = conns[0].get('stats', {}).get('latency_us')
                result['latency'] = max(1, latency_us // 1000)
                # 此节点数据为毫秒，当大于500ms, 只能取到500
                # result['latency_ms'] = item.get('route', {}).get('path_latency', [])
                result['dynamic'] = uri.lower().startswith('txt')
                if uri in fail_peers:
                    fail_peers.remove(uri)
                    success_peers[uri] = result

        return {
            'success': success_peers,
            'fail': fail_peers
        }
    
    except json.JSONDecodeError as e:
        logging.info(f"解析 JSON 失败: {e}")
        raise e
    except Exception as e:
        logging.info(f"检测失败: {e}")
        raise e

def check_peers_available_use_connector(bin_path, rpc_port):
    """检测节点可用(bin_path, rpc端口)"""
    cli_path = os.path.join(bin_path, 'easytier-cli.exe' if sys.platform == 'win32' else 'easytier-cli')

    cmd = [
        cli_path,
        '-p', f'127.0.0.1:{rpc_port}',
        '-o', 'json',
        'connector'
    ]

    try:
        # logging.info(f"执行检测命令: {' '.join(cmd)}")
        logging.info(f"执行节点连接检测")

        # 使用 Popen 替代 run，兼容 Windows Python 3.7
        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'ignore',
        }
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(cmd, **kwargs)

        # 手动实现超时控制
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            logging.info("检测命令超时")
            process.kill()
            process.wait()
            return {'success': [], 'fail': []}

        if process.returncode != 0:
            logging.info(f"检测命令执行失败: {stderr}")
            return {'success': [], 'fail': []}

        data = json.loads(stdout)

        # 失败节点
        fail_peers = []
        # 成功节点
        success_peers = []

        for item in data:
            url = item.get('url', {}).get('url', '')
            if item.get('status') == 0:
                success_peers.append(url)
            else:
                fail_peers.append(url)

        return {
            'success': success_peers,
            'fail': fail_peers
        }

    except json.JSONDecodeError as e:
        logging.info(f"解析 JSON 失败: {e}")
        raise e
    except Exception as e:
        logging.info(f"检测失败: {e}")
        raise e


if __name__ == "__main__":
    run_configs.setup_env()
    log_util.setup_log(enabled_console=True)
    peer_list = peers.public_peers({})
    peer_uris = [peer['uri'] for peer in peer_list]
    aa = check_peers(run_configs.core_dir(), peer_uris, max_wait_second=15)
    print(json.dumps(aa, ensure_ascii=False, indent=2))
