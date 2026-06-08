#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyTier-EUI Server 多平台打包脚本
支持: Windows(x64), Linux(x64/arm64), 统信UOS(x64/arm64)
"""

import os
import subprocess
import sys
import venv
from pathlib import Path

# Fix Windows console encoding for GitHub Actions
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 项目路径
PROJECT_DIR = Path(__file__).parent.absolute()
BUILD_DIR = PROJECT_DIR / "build"
DIST_DIR = PROJECT_DIR / "dist"

def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    print(f"  执行: {cmd}")
    try:
        # Windows 使用 utf-8 编码
        encoding = 'utf-8' if sys.platform == "win32" else None
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, encoding=encoding, errors='replace')
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    if result.stdout:
        print(result.stdout)
    return True

def install_deps(pip_cache_dir:str = ""):
    """安装依赖"""
    print(" 安装依赖...")
    # 检测是否在 CI 环境
    in_ci = os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'
    # 检测是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv or in_ci:

        print(f"  检测到已在 {'虚拟' if in_venv else 'CI' } 环境中，直接安装")
        pip_cmd = "pip"
        python_path = "python" if sys.platform == 'win32' else 'python3'
    else:
        print(f"  检测到不在虚拟环境中，创建Python虚拟环境")
        project_dir = os.path.dirname(os.path.abspath(__file__))
        venv_dir = os.path.join(project_dir, ".venv")
        print(f"  创建虚拟环境: {venv_dir}")
        venv.create(venv_dir, with_pip=True)
        # if not os.path.exists(venv_dir):
        # 确定虚拟环境的 pip 路径
        if sys.platform == "win32":
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
            python_path = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            pip_path = os.path.join(venv_dir, "bin", "pip")
            python_path = os.path.join(venv_dir, "bin", "python")
        pip_cmd = f'"{pip_path}"'
        print(f"  使用虚拟环境 Python: {python_path}")

    print("  更新 pip")
    run_command(f'{python_path} -m pip install --upgrade pip')
    # 安装依赖（带清华镜像）
    mirror = "-i https://pypi.tuna.tsinghua.edu.cn/simple"
    print("  安装 pyinstaller qrcode 依赖")
    if not run_command(f'{pip_cmd} install pyinstaller qrcode {mirror}'):
        raise Exception(f"安装失败: {pip_cmd}")
    pip_cache = ''
    if pip_cache_dir and os.path.exists(pip_cache_dir):
        pip_cache = f"--cache-dir {pip_cache_dir}"
    print("  安装 base 依赖")
    if not run_command(f'{pip_cmd} install {pip_cache} -r requirements-base.txt {mirror}'):
        raise Exception(f"安装失败: {pip_cmd}")

    if sys.platform == "linux":
        print(f"当前是 Linux 环境跳过安装 gui 依赖")
    else:
        print("  安装 gui 依赖")
        if not run_command(f'{pip_cmd} install {pip_cache} -r requirements-gui.txt {mirror}'):
            raise Exception(f"安装失败: {pip_cmd}")
    return python_path, pip_cmd


if __name__ == "__main__":
    os.environ['PYTHONUTF8'] = "1"
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--et_ver', default='', help='easytier 版本号')
    parser.add_argument('--build_ver', default='', help='构建版本号')
    parser.add_argument('--github_proxy_url', default="https://ghfast.top", help='GitHub加速连接')
    parser.add_argument('--pip_cache_dir', default="", help='pip缓存目录')
    args = parser.parse_args()
    et_ver = args.et_ver
    build_ver = args.build_ver
    github_proxy_url = args.github_proxy_url
    pip_cache_dir = args.pip_cache_dir
    print(f"et_ver: {et_ver}")
    print(f"build_ver: {build_ver}")
    print(f"github_proxy_url: {github_proxy_url}")
    print(f"pip_cache_dir: {pip_cache_dir}")

    python_path, pip_cmd = install_deps(pip_cache_dir)
    print("", flush=True)
    build_script_path = os.path.join(os.path.dirname(__file__), "build_core.py")
    result = subprocess.run([str(python_path), build_script_path,
                             "--et_ver", et_ver,
                             "--build_ver", build_ver,
                             "--github_proxy_url", github_proxy_url,
                             ])
    sys.exit(result.returncode)