#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server 多平台打包脚本
支持: Windows(x64), Linux(x64/arm64), 统信UOS(x64/arm64)
"""

import os
import platform
import shutil
import subprocess
import sys
import venv
import zipfile
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
APP_NAME = "EasyTier-EUI"

def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    print(f"执行: {cmd}")
    try:
        kwargs = {
            'shell': True,
            'cwd': cwd,
            'capture_output': True,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'replace',
        }
        if sys.platform == 'win32':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        # Windows 使用 utf-8 编码
        encoding = 'utf-8' if sys.platform == "win32" else None
        result = subprocess.run(cmd, **kwargs)
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False
    if result.stdout:
        print(result.stdout)
    return True

def clean_build():
    """清理构建目录"""
    print("[1/5] 清理构建目录...")
    for dir_path in [BUILD_DIR, DIST_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  删除 {dir_path}")
    # 重新创建构建目录
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

def install_deps():
    """安装依赖"""
    print("[2/5] 安装依赖...")
    # 检测是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print(f"  检测到已在虚拟环境中，直接安装")
        pip_cmd = "pip"
        python_path = "python3"
    else:
        print(f"  检测到不在虚拟环境中，创建Python虚拟环境")
        project_dir = os.path.dirname(os.path.abspath(__file__))
        venv_dir = os.path.join(project_dir, ".venv")
        if not os.path.exists(venv_dir):
            print(f"  创建虚拟环境: {venv_dir}")
            venv.create(venv_dir, with_pip=True)
        # 确定虚拟环境的 pip 路径
        if sys.platform == "win32":
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
            python_path = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            pip_path = os.path.join(venv_dir, "bin", "pip")
            python_path = os.path.join(venv_dir, "bin", "python")
        pip_cmd = f'"{pip_path}"'
        print(f"  使用虚拟环境 Python: {python_path}")

    # print("  更新 pip")
    # run_command(f'{python_path} -m pip install --upgrade pip')
    # # 安装依赖（带清华镜像）
    # mirror = "-i https://pypi.tuna.tsinghua.edu.cn/simple"
    # print("  安装 base 依赖")
    # if not run_command(f'{pip_cmd} install -r requirements-base.txt {mirror}'):
    #     return False
    # print("  安装 gui 依赖")
    # if not run_command(f'{pip_cmd} install -r requirements-gui.txt {mirror}'):
    #     return False
    return True


def build_executable(build_ver:str = None, one_file:bool = True):
    """构建可执行文件"""
    print("[3/5] 开始打包...")

    if build_ver:
        print(f"  写入构建版本号: {build_ver}")
        save_file = str(PROJECT_DIR.joinpath('utils', 'run_configs.py'))
        with open(save_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 替换以 BUILD_VERSION = " 开头的行
        with open(save_file, "w", encoding="utf-8") as f:
            for line in lines:
                if line.startswith('BUILD_VERSION = "'):
                    line = f'BUILD_VERSION = "{build_ver}"\n'
                f.write(line)

    output_name = f"{APP_NAME}"
    
    # 根据平台选择分隔符
    separator = ";" if sys.platform == "win32" else ":"

    cmd = [
        # sys.executable, "-m", "pyinstaller",
        "pyinstaller",
        "--windowed",
        "--onefile" if one_file else "--onedir",  # 单文件
        "--clean",    # 清理缓存
        "--name", output_name,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(BUILD_DIR),
        "--hidden-import", "tomlkit",
        "--hidden-import", "requests",
        "--hidden-import", "psutil",
        "--hidden-import", "actions.configs",
        "--hidden-import", "actions.et_app",
        "--hidden-import", "actions.et_core",
        "--hidden-import", "actions.et_eui",
        "--hidden-import", "actions.monitor",
        "--hidden-import", "actions.peers",
        "--hidden-import", "actions.services",
        "--hidden-import", "actions.settings",
        "--hidden-import", "actions.windows",
        "--hidden-import", "utils.check_peer",
        "--hidden-import", "utils.common_util",
        "--hidden-import", "utils.et_run_info",
        "--hidden-import", "utils.et_util",
        "--hidden-import", "utils.github_util",
        "--hidden-import", "utils.http_util",
        "--hidden-import", "utils.ip_util",
        "--hidden-import", "utils.log_util",
        "--hidden-import", "utils.process_util",
        "--hidden-import", "utils.qrcode_util",
        "--hidden-import", "utils.run_configs",
        "--hidden-import", "utils.security",
        "--hidden-import", "utils.validators",
        "--hidden-import", "http_dispatcher.dispatcher",
        "--add-data", f"{Path(__file__).absolute().parent.parent}/frontend/dist{separator}frontend",
        "--add-data", f"{Path(__file__).absolute().parent.parent}/frontend/dist{separator}frontend",
        "--add-data", f"{PROJECT_DIR.joinpath('assets', 'upgrade.bat')}{separator}assets",
        "--add-data", f"{PROJECT_DIR.joinpath('assets', 'upgrade.sh')}{separator}assets",
    ]

    # ========== 平台特定的 webview 后端处理 ==========
    if sys.platform == "linux":
        print("  [Linux] 不使用 WebView ...")
        cmd.extend([
            "--exclude-module", "webview",
            str(PROJECT_DIR / "http_server.py"),
        ])
    else:
        print("  非 [Linux] 使用 WebView ...")
        if sys.platform == "win32":
            cmd.extend([
                "--uac-admin",
            ])
        # 打包文件的图标路径
        if sys.platform == "win32":
            icon_path = PROJECT_DIR.joinpath('assets', 'icon.ico')
        elif sys.platform == "darwin":
            icon_path = PROJECT_DIR.joinpath('assets', 'icon.icns')
        else:
            icon_path = PROJECT_DIR.joinpath('assets', 'icon.png')

        # 添加图标（如果存在）
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])
        else:
            print(f"  警告: 图标文件不存在: {str(icon_path)}")

        webview_logo_path = os.path.join(PROJECT_DIR, 'assets', 'icon.ico')
        cmd.extend([
            "--hidden-import", "webview",
            "--add-data", f"{webview_logo_path}{separator}assets",
            str(PROJECT_DIR / "main_ui.py"),
        ])
    
    result = run_command(" ".join(cmd), cwd=str(PROJECT_DIR))
    return result, output_name

def get_platform_name():
    """获取 EasyTier 平台标识"""
    system = sys.platform
    machine = os.uname().machine if hasattr(os, 'uname') else platform.machine()
    
    # 系统映射
    sys_map = {
        "win32": "windows",
        "linux": "linux",
        "darwin": "macos"
    }
    
    # 架构映射
    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
        "riscv64": "riscv64",
        "armv7l": "armv7"
    }
    
    sys_name = sys_map.get(system, system)
    arch_name = arch_map.get(machine.lower())
    if not arch_name:
        raise AssertionError(f"不支持的系统架构：: {system} {machine}")
    
    return f"{sys_name}-{arch_name}"

def get_latest_version():
    """获取 EasyTier 最新版本号"""
    import requests
    try:
        response = requests.get("https://api.github.com/repos/EasyTier/EasyTier/releases/latest", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("tag_name", "v2.5.0").replace('v', '')
    except Exception as e:
        print(f"  获取最新版本失败: {e}")
    return "2.5.0"

def download_easytier(version:str=None, proxy_url=None):
    """下载easytier核心"""
    print("[4/5] 下载easytier...")
    
    import requests

    # 获取版本号
    if not version:
        version = get_latest_version()
    print(f"  版本: {version}")
    
    # 获取平台标识
    platform = get_platform_name()
    print(f"  平台: {platform}")
    
    # 构建下载链接
    filename = f"easytier-{platform}-v{version}.zip"
    url = f"https://github.com/EasyTier/EasyTier/releases/download/v{version}/{filename}"
    if proxy_url:
        url = f"{proxy_url}/{url}"
    print(f"  下载: {url}")
    
    # 下载文件
    download_path = BUILD_DIR / filename
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(download_path, 'wb') as f:
            last_percent = -1  # 初始化在循环外
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        current_percent = int(percent)  # 取整
                        # 每增加 1% 打印一次，且只打印一次
                        if current_percent > last_percent:
                            print(f"  进度: {current_percent}%", end='\r')
                            last_percent = current_percent
        
        print(f"\n  下载完成: {download_path}")
        return download_path
        
    except Exception as e:
        print(f"  下载失败: {e}")
        return None

def extract_easytier(zip_path, core_dir):
    """解压easytier到core目录"""
    import zipfile
    
    print(f"  解压到: {core_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 列出zip内容
            files = zip_ref.namelist()
            print(f"  ZIP内容: {files}")
            
            # 解压所有文件
            zip_ref.extractall(core_dir)
            
            # 如果是单层目录，移动到core_dir根目录
            if len(files) > 0:
                first_item = files[0]
                if '/' in first_item:
                    subdir = first_item.split('/')[0]
                    subdir_path = Path(core_dir) / subdir
                    if subdir_path.is_dir():
                        # 移动子目录内容到core_dir
                        ext = ".exe" if sys.platform == "win32" else ""
                        for item in subdir_path.iterdir():
                            target = Path(core_dir) / item.name
                            if target.exists():
                                if target.is_dir():
                                    shutil.rmtree(target)
                                else:
                                    os.remove(target)
                            if item.name in [f'easytier-web{ext}', f'easytier-web-embed{ext}']:
                                continue
                            print(f"  复制: {item.name}")
                            shutil.move(str(item), str(target))
                        # 删除空子目录
                        shutil.rmtree(subdir_path)
        
        # 设置可执行权限（Linux/macOS）
        if sys.platform != "win32":
            for f in Path(core_dir).iterdir():
                if f.is_file():
                    os.chmod(f, 0o755)

        print(f"  解压并复制完成")
        return True
        
    except Exception as e:
        print(f"  解压失败: {e}")
        return False

def copy_output(output_name, et_file, build_ver, one_file:bool):
    """复制输出文件"""
    print("[4/5] 复制输出文件...")
    
    platform_name = get_platform_name()
    output_dir = DIST_DIR.joinpath(f"{APP_NAME}-{platform_name}{'-' + build_ver if build_ver else ""}").joinpath(APP_NAME)
    # output_dir = DIST_DIR.joinpath(f"{APP_NAME}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if one_file:
        # Path(output_dir).mkdir(parents=False, exist_ok=True)
        # 确定可执行文件扩展名
        ext = ".exe" if sys.platform == "win32" else ""
        src_file = DIST_DIR.joinpath(f"{output_name}{ext}")
        if not src_file.exists():
            print(f"  未找到: {src_file}")
            return False
        target_file = output_dir.joinpath(f"{output_name}{ext}")
        shutil.copy2(src_file, target_file)
        print(f"  复制到: {target_file}")
    else:
        src_dir = DIST_DIR.joinpath(APP_NAME)
        if not src_dir.exists():
            print(f"  未找到: {src_dir}")
            return False
        shutil.copytree(src_dir, output_dir, dirs_exist_ok=True)
        pass

    if sys.platform == "linux":
        shutil.copy2(PROJECT_DIR.joinpath('shell', 'start.sh'), output_dir.joinpath('start.sh'))
        shutil.copy2(PROJECT_DIR.joinpath('shell', 'stop.sh'), output_dir.joinpath('stop.sh'))
        output_dir.joinpath('start.sh').chmod(0o777)
        output_dir.joinpath('stop.sh').chmod(0o777)

    core_dir = Path(output_dir).joinpath('core')
    core_dir.mkdir(parents=False, exist_ok=True)
    
    # 解压 easytier 到 core_dir
    if et_file and Path(et_file).exists():
        extract_easytier(et_file, core_dir)
    else:
        print(f"  警告: EasyTier 文件不存在")
        return False
    
    # 压缩：打包 output_dir 及其所有内容
    zipfile_name = DIST_DIR.joinpath(f"{APP_NAME}-{platform_name}{'-' + build_ver if build_ver else ""}.zip")
    with zipfile.ZipFile(zipfile_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 遍历 output_dir 下的所有内容（包括文件和文件夹）
        for item in output_dir.rglob('*'):
            # 计算相对路径（相对于 output_dir，保留 APP_NAME 根目录）
            arch_name = Path(APP_NAME) / item.relative_to(output_dir)
            
            if item.is_dir():
                # 创建目录条目（路径末尾需要加斜杠）
                dir_info = zipfile.ZipInfo(str(arch_name) + '/')
                zf.writestr(dir_info, '')
            elif item.is_file():
                # 打包文件
                zf.write(item, arch_name)
    return True, zipfile_name

def main(et_ver:str=None, github_proxy_url:str=None, build_ver:str="", one_file:bool=True):
    """主函数"""
    print("=" * 50)
    print(f"{APP_NAME} Server 多平台打包")
    print(f"当前平台: {get_platform_name()}")
    print(f"et_ver: {et_ver}")
    print(f"build_ver: {build_ver}")
    print(f"当前Python版本: {platform.python_version()}")
    print(f"当前Python: {sys.executable}")
    print(f"Python 路径: {sys.path}")
    print(f"打包模式：one_file = {one_file}")
    print("=" * 50)

    # 检查 Python
    if sys.version_info < (3, 7):
        print("[错误] 需要 Python 3.7+")
        sys.exit(1)

    # 执行构建步骤
    clean_build()

    if not install_deps():
        print("[错误] 依赖安装失败")
        sys.exit(1)

    result, output_name = build_executable(build_ver, one_file)
    if not result:
        print("[错误] 打包失败")
        sys.exit(1)

    et_file = download_easytier(version=et_ver, proxy_url=github_proxy_url)
    if not et_file:
        print(f"[错误] 下载easytier失败")
        sys.exit(1)

    result, output_name = copy_output(output_name, et_file, build_ver, one_file)
    if not result:
        print("[错误] 复制文件失败")
        sys.exit(1)

    print("=" * 50)
    print("打包完成!")
    print(f"输出: {output_name}")
    print("=" * 50)

if __name__ == "__main__":
    os.environ['PYTHONUTF8'] = "1"
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--et_ver', default='', help='easytier 版本号', required=False)
    parser.add_argument('--build_ver', default='', help='构建版本号', required=False)
    parser.add_argument('--github_proxy_url', default="https://ghfast.top", help='GitHub加速连接', required=False)
    args = parser.parse_args()
    et_ver = args.et_ver
    build_ver = args.build_ver
    github_proxy_url = args.github_proxy_url
    print(f"et_ver: {et_ver}")
    print(f"github_proxy_url: {github_proxy_url}")

    main(et_ver, github_proxy_url, build_ver, one_file=True)
