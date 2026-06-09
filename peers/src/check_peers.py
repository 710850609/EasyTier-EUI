#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyTier 节点检测工具
使用 easytier-core 和 easytier-cli 检测节点连通性和延迟
"""

from gc import disable
import os
import sys
import subprocess
import time
import re
import json
import urllib.request
import zipfile
import shutil
import socket
import random
import string
import signal

def get_random_string(length=16):
    """获取随机字符串（指定长度）"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_available_port(start_port=15888, end_port=65535):
    """获取可用端口(选定范围)"""
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"在范围 {start_port}-{end_port} 内找不到可用端口")


def get_easytier_bin_path():
    """获取easytier执行文件路径()"""
    peers_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_path = os.path.join(peers_dir, 'bin')
    
    # 确定可执行文件名
    if sys.platform == 'win32':
        core_filename = 'easytier-core.exe'
        cli_filename = 'easytier-cli.exe'
    else:
        core_filename = 'easytier-core'
        cli_filename = 'easytier-cli'
    
    core_path = os.path.join(bin_path, core_filename)
    cli_path = os.path.join(bin_path, cli_filename)
    
    # 如果 easytier-core 不存在，则下载
    if not os.path.exists(core_path):
        print(f"easytier-core 不存在，开始下载...")
        download_easytier(bin_path)
    
    return bin_path


def download_easytier(bin_path):
    """下载 easytier 并解压到指定目录"""
    easytier_core_version = '2.5.0'
    github_proxy = "https://ghfast.top/"
    
    # 确定下载地址
    if sys.platform == 'win32':
        download_url = f'{github_proxy}https://github.com/EasyTier/EasyTier/releases/download/v{easytier_core_version}/easytier-windows-x86_64-v{easytier_core_version}.zip'
        core_filename = 'easytier-core.exe'
        cli_filename = 'easytier-cli.exe'
    else:
        download_url = f'{github_proxy}https://github.com/EasyTier/EasyTier/releases/download/v{easytier_core_version}/easytier-linux-x86_64-v{easytier_core_version}.zip'
        core_filename = 'easytier-core'
        cli_filename = 'easytier-cli'
    
    # 创建临时目录
    peers_dir = os.path.dirname(bin_path)
    temp_dir = os.path.join(peers_dir, 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(bin_path, exist_ok=True)
    
    zip_path = os.path.join(temp_dir, 'easytier.zip')
    
    try:
        print(f"下载地址: {download_url}")
        urllib.request.urlretrieve(download_url, zip_path)
        print("下载完成，开始解压...")
        
        # 解压文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        print("解压完成")
        
        # 查找并移动可执行文件
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file == core_filename:
                    src = os.path.join(root, file)
                    dst = os.path.join(bin_path, core_filename)
                    shutil.move(src, dst)
                    print(f"已移动 {core_filename} 到: {dst}")
                elif file == cli_filename:
                    src = os.path.join(root, file)
                    dst = os.path.join(bin_path, cli_filename)
                    shutil.move(src, dst)
                    print(f"已移动 {cli_filename} 到: {dst}")
        
        # Windows 还需要移动 Packet.dll
        if sys.platform == 'win32':
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == 'Packet.dll':
                        src = os.path.join(root, file)
                        dst = os.path.join(bin_path, 'Packet.dll')
                        shutil.move(src, dst)
                        print(f"已移动 Packet.dll 到: {dst}")
                        break
        
        # Linux 添加执行权限
        if sys.platform != 'win32':
            core_path = os.path.join(bin_path, core_filename)
            cli_path = os.path.join(bin_path, cli_filename)
            if os.path.exists(core_path):
                os.chmod(core_path, 0o755)
            if os.path.exists(cli_path):
                os.chmod(cli_path, 0o755)
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print("清理临时文件完成")
        
    except Exception as e:
        print(f"下载或解压失败: {e}")
        raise


def check_peers(peer_list, max_wait_time = 10):
    """检测节点(节点list)"""
    bin_path = get_easytier_bin_path()
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
    
    print(f"启动检测进程，RPC端口: {rpc_port}")
    print(f"检测节点: {peer_list}")
    
    # 启动进程
    print(f"启动检测进程: {' '.join(cmd)}")
    
    def start_process():
        print(" ".join(cmd))
        if sys.platform == 'win32':
            # Windows: 使用 CREATE_NEW_PROCESS_GROUP 来允许终止进程树
            return subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            return subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
    
    # 启动进程
    process = start_process()
    
    # 检查进程是否成功启动
    time.sleep(0.5)
    if process.poll() is not None:
        print(f"进程启动失败，返回码: {process.returncode}")
        return {'success': [], 'fail': peer_list}
    
    print(f"进程启动成功，PID: {process.pid}")
    
    # 等待 RPC 服务就绪
    print(f"等待 RPC 服务就绪 (127.0.0.1:{rpc_port})...")
    rpc_ready = False
    rpc_check_start = time.time()
    rpc_check_timeout = 10  # 最多等待10秒
    while (time.time() - rpc_check_start) < rpc_check_timeout:
        if process.poll() is not None:
            print(f"进程已退出，返回码: {process.returncode}")
            return {'success': [], 'fail': peer_list}
        
        # 尝试连接 RPC 端口
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', rpc_port))
            sock.close()
            if result == 0:
                rpc_ready = True
                print(f"RPC 服务已就绪")
                break
        except:
            pass
        time.sleep(0.5)
    

    start_check_time = time.time()
    result = None
    
    try:
        if not rpc_ready:
            raise Exception(f"EasyTier 服务未在 {rpc_check_timeout} 秒内就绪")
        while (time.time() - start_check_time) < max_wait_time:
            # 检查进程是否还在运行
            if process.poll() is not None:
                raise Exception(f"EasyTier 服务已退出，返回码: {process.returncode}")
            
            time.sleep(2)
            result = check_peers_available(bin_path, rpc_port)
            # fail_list = result['fail'] if len(result['fail']) > 0 else peer_list
            result['fail'] = [ item for item in peer_list if item not in result.get('success', [])]
            if len(result['fail']) == 0:
                break
            print(f"继续等待未连接节点: {result['fail']}")
        
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


def check_peers_available(bin_path, rpc_port):
    """检测节点可用(bin_path, rpc端口)"""
    cli_path = os.path.join(bin_path, 'easytier-cli.exe' if sys.platform == 'win32' else 'easytier-cli')
    
    cmd = [
        cli_path,
        '-p', f'127.0.0.1:{rpc_port}',
        '-o', 'json',
        'connector'
    ]
    
    try:
        print(f"执行检测命令: {' '.join(cmd)}")
        
        # 使用 Popen 替代 run，兼容 Windows Python 3.7
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 手动实现超时控制
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            print("检测命令超时")
            process.kill()
            process.wait()
            return {'success': [], 'fail': []}
        
        if process.returncode != 0:
            print(f"检测命令执行失败: {stderr}")
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
        print(f"解析 JSON 失败: {e}")
        raise e
    except Exception as e:
        print(f"检测失败: {e}")
        raise e


def check_peer_latency(uri):
    """检测节点延迟（节点uri）"""
    bin_path = get_easytier_bin_path()
    core_path = os.path.join(bin_path, 'easytier-core.exe' if sys.platform == 'win32' else 'easytier-core')
    
    rpc_port = get_available_port(16888, 65535)
    random_string = get_random_string(16)
    
    # 构建命令
    cmd = [
        core_path,
        '--console-log-level', 'ERROR',
        '--no-listener',
        '--private-mode', 'true',
        '-r', str(rpc_port),
        '--network-name', random_string,
        '--network-secret', random_string,
        '-p', uri
    ]
    
    print(f"启动延迟检测进程，RPC端口: {rpc_port}")
    print(f"检测节点: {uri}")
    
    # 启动进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='ignore',
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
    )
    
    try:
        # 等待 3 秒
        time.sleep(3)
        
        # 执行检测命令
        cli_path = os.path.join(bin_path, 'easytier-cli.exe' if sys.platform == 'win32' else 'easytier-cli')
        check_cmd = [
            cli_path,
            '-p', f'127.0.0.1:{rpc_port}',
            '-o', 'json',
            'peer'
        ]
        
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=5)
        
        info = {'uri': uri}
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if isinstance(data, list) and len(data) > 0:
                    # 取第一个对等节点的信息
                    for peer_info in data:
                        if peer_info["cost"] == "Local":
                            continue
                        for key, value in peer_info.items():
                            if key in ["hostname", 'lat_ms', 'loss_rate', 'cost']:
                                info[key] = value
            except json.JSONDecodeError:
                pass
        
        return info
    
    finally:
        # 停止进程
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


def check():
    """主函数"""
    src_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../peer-source.txt'))
    meta_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../peer-txt-meta.json'))
    print(f"检测节点文件: {src_file}")    
    with open(src_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        peer_source = [line.strip() for line in lines if line.strip()]
    
    print("=" * 60)
    print("检测节点连通性")
    print("=" * 60)
    result = check_peers(peer_source, 20)
    print("检测结果: " + json.dumps(result, ensure_ascii=False, indent=2))
    success_peers = result['success'] or []
    peer_meta = {}
    with open(meta_file, 'r', encoding='utf-8') as f:
        peer_meta = json.load(f)
    peer_meta['count'] = len(success_peers)
    peer_meta['updateTime'] = int(time.time())
    exists_uris = set()
    unused_txts = []
    for key in peer_meta['peers'].keys():
        uri = peer_meta['peers'][key].get('uri', '')
        exists_uris.add(uri)
        if uri in success_peers:
            peer_meta['peers'][key]['status'] = 1
            peer_meta['peers'][key]['updateTime'] = int(time.time())
        else:
            if peer_meta['peers'][key]['status'] == 0 and uri != '':
                print(f"节点失效，释放txt: {key} --> {uri}")
            peer_meta['peers'][key]['status'] = 0
            peer_meta['peers'][key]['updateTime'] = int(time.time())
            unused_txts.append(key)
    for uri in success_peers:
        if uri not in exists_uris:
            if len(unused_txts) > 0:
                unused_txt = unused_txts.pop(0)
                peer_meta['peers'][unused_txt] = {'status': 1, 'updateTime': int(time.time()), 'uri': uri}
                print(f"复用失效txt: {unused_txt} --> {uri}")
            else:
                print(f"没有可用txt保存节点: {uri}")
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(peer_meta, f, ensure_ascii=False, indent=2)
    print(f"更新完成，当前节点数: {peer_meta['count']}")



def test():
    """主函数"""
    # 示例用法
    with open(f'../peer-source.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        test_peers = [line.strip() for line in lines if line.strip()]
    
    test_peers = [
        'tcp://kddi10gbps.xzcloudnode.sbs:49784',
    ]
    
    print("=" * 60)
    print("检测节点连通性")
    print("=" * 60)
    result = check_peers(test_peers)
    print(f"成功: {result['success']}")
    print(f"失败: {result['fail']}")
    
    print("\n" + "=" * 60)
    print("检测节点延迟")
    print("=" * 60)
    for peer in test_peers:
        info = check_peer_latency(peer)
        print(f"节点: {info}")


if __name__ == "__main__":
    check()
