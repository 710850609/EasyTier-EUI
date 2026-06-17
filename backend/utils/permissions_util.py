#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import logging
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List

import psutil


def is_frozen() -> bool:
    """检查当前是否运行在 PyInstaller 打包环境中"""
    return getattr(sys, 'frozen', False)


def get_resource_path(relative_path: str, script_file: Optional[str] = None) -> str:
    """
    获取资源文件的绝对路径，兼容 PyInstaller 打包和源码运行两种模式。

    在提权脚本中使用此函数来定位相对资源路径：
      - 非打包模式：基于脚本所在目录解析
      - 打包模式：基于 sys._MEIPASS（PyInstaller 临时解压目录）解析

    Args:
        relative_path: 相对于脚本/资源根目录的路径
        script_file: （非打包模式时）脚本的 __file__，用于定位脚本所在目录。
                     打包模式下忽略此参数。
    """
    if is_frozen():
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        if script_file:
            base_path = os.path.dirname(os.path.abspath(script_file))
        else:
            base_path = os.getcwd()
    return os.path.normpath(os.path.join(base_path, relative_path))


def is_admin() -> bool:
    """检查当前是否拥有管理员（Windows）或 root（Unix）权限"""
    if sys.platform == 'win32':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:
        return os.geteuid() == 0


def elevate() -> None:
    """权限不足时，通过系统原生方式提权并重新运行当前程序"""
    if is_admin():
        return

    # ── Windows ──
    if sys.platform == 'win32':
        # 构建完整的命令行参数（包含程序路径）
        args = subprocess.list2cmdline([sys.executable] + sys.argv[1:])
        # 使用 SW_HIDE (0) 避免弹出控制台窗口
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, args, None, 0
        )
        if ret <= 32:
            raise PermissionError(f"UAC 提权失败或用户取消 (错误码: {ret})")
        sys.exit(0)

    # ── macOS ──
    elif sys.platform == 'darwin':
        # 使用 AppleScript 弹出系统密码框，不依赖终端
        cmd_str = " ".join(shlex.quote(p) for p in [sys.executable] + sys.argv[1:])
        script = f'do shell script {shlex.quote(cmd_str)} with administrator privileges'

        try:
            subprocess.run(["osascript", "-e", script], check=True)
        except subprocess.CalledProcessError as e:
            raise PermissionError("用户取消授权或密码错误") from e

        # osascript 会等待子进程结束，原进程直接退出即可
        sys.exit(0)

    # ── Linux ──
    else:
        # 优先 pkexec：图形化密码框，双击运行也能用
        if shutil.which("pkexec"):
            os.execvp("pkexec", ["pkexec", sys.executable] + sys.argv[1:])

        # 回退 sudo：仅在检测到终端时可用
        elif shutil.which("sudo") and sys.stdin.isatty():
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv[1:])

        else:
            raise RuntimeError(
                "无法提权：未安装 pkexec（图形认证），"
                "或无终端环境无法使用 sudo。请在终端中运行本程序。"
            )


class ServerHandle:
    """统一的服务/进程句柄，封装停止操作，调用方无需关心底层进程类型"""

    def __init__(self, server=None, proc=None):
        self._server = server
        self._proc = proc

    @property
    def pid(self):
        if self._proc is not None:
            return self._proc.pid
        return os.getpid()

    def stop(self):
        if self._proc is not None:
            self._proc.terminate()
        elif self._server is not None:
            self._server.shutdown()


def run_elevated_script(
    script_path: str,
    args: Optional[List[str]] = None,
    pid_file: Optional[str] = None,
    show_window: bool = False,
) -> Optional['ServerHandle']:
    """
    以独立进程提权运行指定的 Python 脚本，返回 ServerHandle 对象。

    自动兼容 PyInstaller 打包和非打包两种模式：
      - 非打包模式：使用当前 Python 解释器直接执行 .py 脚本
      - 打包模式：使用打包后的可执行文件，通过 --elevated-run 参数
        指定要执行的脚本路径，脚本内的资源路径可通过
        ``ELEVATED_SCRIPT_DIR`` 环境变量获取。

    返回的 ServerHandle 对象统一控制进程生命周期::

        handle = run_elevated_script("worker.py")
        if handle:
            handle.stop()  # 调用 terminate() 终止进程

    Args:
        script_path: 要执行的 Python 脚本路径
        args: 传递给脚本的额外命令行参数
        pid_file: 可选，PID 文件路径，用于崩溃恢复时查找进程
        show_window: Windows 下是否显示控制台窗口（默认隐藏）

    Returns:
        psutil.Process 对象，失败返回 None

    Raises:
        FileNotFoundError: 脚本文件不存在
        PermissionError: 提权失败或用户取消
        RuntimeError: 平台不支持
    """
    if getattr(sys, 'frozen', False) and not script_path.startswith(sys._MEIPASS):
        script_path = os.path.join(sys._MEIPASS, script_path)
    script_path = os.path.abspath(script_path)
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"脚本文件不存在: {script_path}")

    if args is None:
        args = []

    script_dir = os.path.dirname(script_path)

    if is_frozen():
        return _run_elevated_frozen(script_path, args, pid_file, script_dir, show_window)
    else:
        return _run_elevated_source(script_path, args, pid_file, script_dir, show_window)


def run_elevated_module(
    module_name: str,
    args: Optional[List[str]] = None,
    pid_file: Optional[str] = None,
    show_window: bool = False,
    working_dir: Optional[str] = None,
) -> Optional['ServerHandle']:
    """
    以独立进程提权运行指定的 Python **模块**（而非 .py 文件），返回
    ServerHandle 对象。通过 ``import`` / ``runpy.run_module`` 加载模块，
    天然兼容 PyInstaller 打包模式（.pyc 被打包，无需 .py 源文件）。

    与 ``run_elevated_script()`` 的区别：
      - run_elevated_script: 入参是 .py 文件路径，打包后源文件不在磁盘上会失败
      - run_elevated_module: 入参是模块名，打包后通过 import 机制仍可用

    非打包模式：通过 ``python -c "import runpy; runpy.run_module(...)"`` 启动
    打包模式：  通过 ``app.exe --elevated-module module_name`` 启动

    Args:
        module_name: Python 模块名，如 'http_server'、'main_ui'
        args: 传递给模块的额外命令行参数（设置到 sys.argv[1:]）
        pid_file: 可选，PID 文件路径
        show_window: Windows 下是否显示控制台窗口（默认隐藏）
        working_dir: 工作目录，默认模块所在目录。打包模式下忽略，
                     由 ELEVATED_WORKING_DIR 环境变量传递。

    Returns:
        ServerHandle 对象，调用 handle.stop() 终止进程；失败返回 None

    Raises:
        PermissionError: 提权失败或用户取消
        RuntimeError: 平台不支持
    """
    import json
    import importlib.util

    if args is None:
        args = []

    if working_dir is None:
        if is_frozen():
            # 打包模式：工作目录为可执行文件所在目录，而非 _MEIPASS 临时目录
            working_dir = os.path.dirname(sys.executable)
        else:
            try:
                spec = importlib.util.find_spec(module_name)
                if spec and spec.origin:
                    working_dir = os.path.dirname(os.path.abspath(spec.origin))
                else:
                    working_dir = os.getcwd()
            except (ImportError, ValueError):
                working_dir = os.getcwd()

    if is_frozen():
        # 打包模式：通过可执行文件 + --elevated-module 参数
        cmd_parts = [sys.executable, '--elevated-module', module_name] + args
        env = os.environ.copy()
        env['ELEVATED_WORKING_DIR'] = working_dir
    else:
        # 非打包模式：通过 python -c 内联脚本，兼容所有 shell 转义
        # pkexec/sudo 会重置环境，需显式注入 sys.path 确保模块可被找到
        argv_json = json.dumps([module_name] + args, ensure_ascii=False)
        code = (
            f'import sys, json, runpy, traceback\n'
            f'try:'
            f' sys.path.insert(0, {working_dir!r});'
            f' sys.argv = json.loads({argv_json!r});'
            f' runpy.run_module({module_name!r}, run_name="__main__")\n'
            f'except Exception:'
            f' traceback.print_exc();'
            f' import time; time.sleep(5);'
        )
        cmd_parts = [sys.executable, '-c', code]
        env = os.environ.copy()
        # 兜底：同时通过环境变量传递 PYTHONPATH
        existing_path = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = f'{working_dir}{os.pathsep}{existing_path}' if existing_path else working_dir

    if sys.platform == 'win32':
        return _elevate_windows_subprocess(cmd_parts, pid_file, working_dir, show_window, extra_env=env)
    elif sys.platform == 'darwin':
        return _elevate_macos_subprocess(cmd_parts, pid_file, working_dir, extra_env=env)
    else:
        return _elevate_linux_subprocess(cmd_parts, pid_file, working_dir, extra_env=env)


def _run_elevated_source(
    script_path: str,
    args: List[str],
    pid_file: Optional[str],
    script_dir: str,
    show_window: bool,
) -> Optional['ServerHandle']:
    """非打包模式：直接用 Python 解释器执行脚本"""
    cmd_parts = [sys.executable, script_path] + args

    if sys.platform == 'win32':
        return _elevate_windows_subprocess(cmd_parts, pid_file, script_dir, show_window)
    elif sys.platform == 'darwin':
        return _elevate_macos_subprocess(cmd_parts, pid_file, script_dir)
    else:
        return _elevate_linux_subprocess(cmd_parts, pid_file, script_dir)


def _run_elevated_frozen(
    script_path: str,
    args: List[str],
    pid_file: Optional[str],
    script_dir: str,
    show_window: bool,
) -> Optional['ServerHandle']:
    """
    PyInstaller 打包模式：通过可执行文件 + --elevated-run 参数来运行脚本。

    被提权启动的可执行文件需要在入口处调用 handle_elevated_run() 来识别
    并执行指定的脚本。同时设置 ELEVATED_SCRIPT_DIR 环境变量，供脚本内
    通过 get_resource_path() 解析相对资源路径。
    """
    cmd_parts = [sys.executable, '--elevated-run', script_path] + args

    # 传递脚本所在目录，供子进程内的 get_resource_path 使用
    env = os.environ.copy()
    env['ELEVATED_SCRIPT_DIR'] = script_dir

    if sys.platform == 'win32':
        return _elevate_windows_subprocess(cmd_parts, pid_file, script_dir, show_window, extra_env=env)
    elif sys.platform == 'darwin':
        return _elevate_macos_subprocess(cmd_parts, pid_file, script_dir, extra_env=env)
    else:
        return _elevate_linux_subprocess(cmd_parts, pid_file, script_dir, extra_env=env)


# ── Windows ShellExecuteEx 结构体 ──
class _SHELLEXECUTEINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("fMask", ctypes.c_ulong),
        ("hwnd", ctypes.c_void_p),
        ("lpVerb", ctypes.c_wchar_p),
        ("lpFile", ctypes.c_wchar_p),
        ("lpParameters", ctypes.c_wchar_p),
        ("lpDirectory", ctypes.c_wchar_p),
        ("nShow", ctypes.c_int),
        ("hInstApp", ctypes.c_void_p),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", ctypes.c_wchar_p),
        ("hkeyClass", ctypes.c_void_p),
        ("dwHotKey", ctypes.c_ulong),
        ("hIconOrMonitor", ctypes.c_void_p),
        ("hProcess", ctypes.c_void_p),
    ]

_SEE_MASK_NOCLOSEPROCESS = 0x00000040


def _elevate_windows_subprocess(
    cmd_parts: List[str],
    pid_file: Optional[str],
    working_dir: str,
    show_window: bool,
    extra_env: Optional[dict] = None,
) -> Optional['ServerHandle']:
    """Windows：使用 ShellExecuteExW + runas 提权，直接返回子进程 PID"""
    exe = cmd_parts[0]
    params = subprocess.list2cmdline(cmd_parts[1:])
    sw_mode = 1 if show_window else 0  # SW_SHOWNORMAL / SW_HIDE

    # 环境变量通过父进程 os.environ 传递给 ShellExecuteEx 启动的子进程
    if extra_env:
        for key, value in extra_env.items():
            os.environ[key] = value

    sei = _SHELLEXECUTEINFOW()
    sei.cbSize = ctypes.sizeof(_SHELLEXECUTEINFOW)
    sei.fMask = _SEE_MASK_NOCLOSEPROCESS
    sei.lpVerb = "runas"
    sei.lpFile = exe
    sei.lpParameters = params
    sei.lpDirectory = working_dir
    sei.nShow = sw_mode

    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei)):
        error_code = ctypes.windll.kernel32.GetLastError()
        raise PermissionError(f"UAC 提权失败或用户取消 (错误码: {error_code})")

    pid = None
    if sei.hProcess:
        pid = ctypes.windll.kernel32.GetProcessId(sei.hProcess)
        ctypes.windll.kernel32.CloseHandle(sei.hProcess)

    logging.info(f"已通过 UAC 提权启动: {exe} {params}")
    logging.info(f"工作目录: {working_dir}, PID={pid}")

    if pid and pid_file:
        Path(pid_file).parent.mkdir(parents=True, exist_ok=True)
        Path(pid_file).write_text(str(pid))

    return ServerHandle(proc=psutil.Process(pid)) if pid else None


def _elevate_macos_subprocess(
    cmd_parts: List[str],
    pid_file: Optional[str],
    working_dir: str,
    extra_env: Optional[dict] = None,
) -> Optional['ServerHandle']:
    """macOS：使用 osascript 提权，nohup 后台启动，通过 echo $! 捕获 PID"""
    env_prefix = ""
    if extra_env:
        env_parts = [f"{k}={shlex.quote(v)}" for k, v in extra_env.items()]
        env_prefix = " ".join(env_parts) + " "

    cmd_str = " ".join(shlex.quote(p) for p in cmd_parts)
    # nohup 后台运行 + echo $! 捕获 PID，osascript 立即返回
    full_cmd = (
        f"cd {shlex.quote(working_dir)} && "
        f"nohup {env_prefix}{cmd_str} & echo $!"
    )
    applescript = (
        f'do shell script {shlex.quote(full_cmd)}'
        f' with administrator privileges'
    )

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        pid_str = result.stdout.strip()
        pid = int(pid_str) if pid_str else None

        logging.info(f"已通过 osascript 提权启动 PID={pid}，工作目录: {working_dir}")

        if pid and pid_file:
            Path(pid_file).parent.mkdir(parents=True, exist_ok=True)
            Path(pid_file).write_text(str(pid))

        return ServerHandle(proc=psutil.Process(pid)) if pid else None
    except subprocess.CalledProcessError as e:
        raise PermissionError("用户取消授权或密码错误") from e
    except ValueError:
        logging.warning(f"无法解析 osascript 返回的 PID: {pid_str}")
        return None


def _elevate_linux_subprocess(
    cmd_parts: List[str],
    pid_file: Optional[str],
    working_dir: str,
    extra_env: Optional[dict] = None,
) -> Optional['ServerHandle']:
    """Linux：使用 pkexec 或 sudo 提权启动子进程"""
    env_vars = {}
    if extra_env:
        env_vars.update(extra_env)
    env_vars['PWD'] = working_dir

    env_prefix = " ".join(f"{k}={shlex.quote(v)}" for k, v in env_vars.items())
    cmd_str = " ".join(shlex.quote(p) for p in cmd_parts)
    log_file = "/tmp/easytier_elevated.log"
    # sh -c 包装：nohup 后台启动 + echo $! 返回 PID，认证完立即返回
    wrapper = (
        f"cd {shlex.quote(working_dir)} && "
        f"{env_prefix} nohup {cmd_str} > {shlex.quote(log_file)} 2>&1 & echo $!"
    )

    # 优先 pkexec（桌面环境图形认证），失败则 fallback 到 sudo（SSH/终端认证）
    # 无桌面环境时直接跳过 pkexec，避免白输一次密码
    pid = None
    last_error = None
    has_display = bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))

    if has_display and shutil.which("pkexec"):
        try:
            # pkexec 密码提示由 Polkit agent 写 /dev/tty，不经过 stderr
            result = subprocess.run(
                ["pkexec", "sh", "-c", wrapper],
                stdout=subprocess.PIPE, stderr=None, text=True, check=True,
            )
            pid = int(result.stdout.strip()) if result.stdout.strip() else None
        except subprocess.CalledProcessError as e:
            last_error = f"pkexec 认证失败: {e.stderr.strip()}"
            logging.warning(last_error)

    if pid is None and shutil.which("sudo") and sys.stdin.isatty():
        try:
            # sudo 密码提示写 stderr，必须让它走终端，否则用户看不到提示
            result = subprocess.run(
                ["sudo", "sh", "-c", wrapper],
                stdout=subprocess.PIPE, stderr=None, text=True, check=True,
            )
            pid = int(result.stdout.strip()) if result.stdout.strip() else None
        except subprocess.CalledProcessError as e:
            last_error = f"sudo 认证失败: {e.stderr.strip()}"
            logging.warning(last_error)

    if not pid:
        raise RuntimeError(
            f"提权失败: {last_error or '无法获取子进程 PID'}。"
            "请确保已安装 pkexec 或 sudo，并具有管理员权限。"
        )

    if pid_file:
        Path(pid_file).parent.mkdir(parents=True, exist_ok=True)
        Path(pid_file).write_text(str(pid))

    logging.info(f"已提权启动进程 PID={pid}，工作目录: {working_dir}")
    # 等待子进程完全启动，避免竞态导致 psutil.Process 找不到
    for _ in range(10):
        time.sleep(0.1)
        try:
            return ServerHandle(proc=psutil.Process(pid))
        except psutil.NoSuchProcess:
            continue
    logging.error(f"提权进程 PID={pid} 启动后立即退出，请检查 {log_file}")
    return None


def handle_elevated_run():
    """
    处理 PyInstaller 打包模式下的提权执行（兼容脚本文件和模块）。

    在程序入口（main 函数）中调用此函数。支持两种模式：
      - ``--elevated-run <脚本路径>``: 执行 .py 文件路径（兼容旧代码）
      - ``--elevated-module <模块名>``: 执行 Python 模块（推荐，兼容打包后）

    用法示例（在 __main__.py 或主入口中）::

        from utils.permissions_util import handle_elevated_run
        handle_elevated_run()
        # 如果是从 --elevated-run 或 --elevated-module 进来的，
        # 上面已经 exit；否则继续正常启动流程
    """
    # 优先处理 --elevated-module
    if '--elevated-module' in sys.argv:
        try:
            idx = sys.argv.index('--elevated-module')
            if idx + 1 >= len(sys.argv):
                logging.error("--elevated-module 缺少模块名参数")
                sys.exit(1)

            module_name = sys.argv[idx + 1]
            # 剩余参数传递给模块
            module_args = sys.argv[idx + 2:]

            # 设置工作目录（从环境变量获取）
            working_dir = os.environ.get('ELEVATED_WORKING_DIR', os.getcwd())
            os.chdir(working_dir)

            logging.info(f"[Elevated] 正在执行模块: {module_name}")
            logging.info(f"[Elevated] 工作目录: {working_dir}")
            logging.info(f"[Elevated] 模块参数: {module_args}")

            # 使用 importlib 执行模块，避免 runpy 在模块已被导入时的警告
            import importlib
            original_argv = sys.argv
            sys.argv = [module_name] + module_args
            try:
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    raise ImportError(f"No module named {module_name}")
                mod = importlib.util.module_from_spec(spec)
                mod.__name__ = '__main__'
                sys.modules[module_name] = mod
                spec.loader.exec_module(mod)
            finally:
                sys.argv = original_argv

            sys.exit(0)
        except Exception as e:
            logging.exception(f"[Elevated] 执行模块失败: {e}")
            sys.exit(1)

    if '--elevated-run' not in sys.argv:
        return

    try:
        idx = sys.argv.index('--elevated-run')
        if idx + 1 >= len(sys.argv):
            logging.error("--elevated-run 缺少脚本路径参数")
            sys.exit(1)

        script_path = sys.argv[idx + 1]
        # 剩余参数传递给脚本
        script_args = sys.argv[idx + 2:]

        # 设置脚本工作目录（从环境变量获取，由父进程设置）
        script_dir = os.environ.get('ELEVATED_SCRIPT_DIR', os.path.dirname(script_path))
        os.chdir(script_dir)

        logging.info(f"[Elevated] 正在执行脚本: {script_path}")
        logging.info(f"[Elevated] 工作目录: {script_dir}")
        logging.info(f"[Elevated] 脚本参数: {script_args}")

        # 使用 runpy 执行脚本
        import runpy
        original_argv = sys.argv
        sys.argv = [script_path] + script_args
        try:
            runpy.run_path(script_path, run_name='__main__')
        finally:
            sys.argv = original_argv

        sys.exit(0)
    except Exception as e:
        logging.exception(f"[Elevated] 执行脚本失败: {e}")
        sys.exit(1)


# ========== 使用示例 ==========
if __name__ == "__main__":
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="permissions_util 功能演示")
    parser.add_argument(
        "--demo", choices=["elevate", "run-script", "stop", "resource-path"],
        default="run-script", help="选择演示功能"
    )
    parser.add_argument("--pid-file", help="停止进程时使用的 PID 文件路径")
    parser.add_argument("--pid", type=int, help="停止进程时使用的 PID")
    demo_args, _ = parser.parse_known_args()

    # ---- handle_elevated_run() 调用示例 ----
    handle_elevated_run()

    if demo_args.demo == "elevate":
        # 示例 1：提权运行当前程序
        print("当前管理员状态:", is_admin())
        if not is_admin():
            print("正在请求提权...")
            elevate()
        print("✅ 已以高权限运行")

    elif demo_args.demo == "run-script":
        # 示例 2：以独立进程提权运行脚本，返回 psutil.Process 对象
        demo_script = os.path.join(tempfile.gettempdir(), "_demo_elevated_worker.py")
        with open(demo_script, "w", encoding="utf-8") as f:
            f.write("""\
import os, sys, time
from utils.permissions_util import is_admin, get_resource_path

print(f"[Worker] PID={os.getpid()}, 管理员={is_admin()}")
print(f"[Worker] frozen={getattr(sys, 'frozen', False)}")
print(f"[Worker] 资源路径(data/config.json)={get_resource_path('data/config.json', __file__)}")
print("[Worker] 执行管理员操作中...")
time.sleep(2)
print("[Worker] 完成")
""")
        pid_file = os.path.join(tempfile.gettempdir(), "_demo_elevated.pid")
        print(f"演示脚本: {demo_script}")
        print(f"打包模式: {is_frozen()}")

        proc = run_elevated_script(
            demo_script,
            args=["--worker-id", "demo-001"],
            pid_file=pid_file,
            show_window=True,
        )
        if proc is None:
            print("❌ 启动失败")
        else:
            print(f"✅ 已启动, PID={proc.pid}, is_running={proc.is_running()}")
            print(f"   PID 文件: {pid_file}")
            print(f"   使用 proc.terminate() / proc.kill() 停止进程")

    elif demo_args.demo == "stop":
        # 示例 3：通过 psutil.Process 或 PID 文件停止进程
        proc = None
        if demo_args.pid_file and Path(demo_args.pid_file).exists():
            pid = int(Path(demo_args.pid_file).read_text().strip().split()[0])
            proc = psutil.Process(pid)
        elif demo_args.pid:
            proc = psutil.Process(demo_args.pid)

        if proc is None:
            print("请通过 --pid-file 或 --pid 指定要停止的进程")
            print("示例: python permissions_util.py --demo stop --pid 12345")
            print("示例: python permissions_util.py --demo stop --pid-file /tmp/demo.pid")
        elif not proc.is_running():
            print(f"进程 PID={proc.pid} 已不存在")
        else:
            print(f"正在停止 PID={proc.pid}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
                print("✅ 优雅关闭成功")
            except psutil.TimeoutExpired:
                print("超时，强制终止...")
                proc.kill()
                proc.wait()
                print("✅ 强制终止成功")

    elif demo_args.demo == "resource-path":
        # 示例 4：演示 get_resource_path
        print(f"打包模式: {is_frozen()}")
        print(f"sys.executable: {sys.executable}")
        print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
        print(f"get_resource_path('data/config.json', __file__):")
        print(f"  -> {get_resource_path('data/config.json', __file__)}")
        print(f"get_resource_path('data/config.json'):")
        print(f"  -> {get_resource_path('data/config.json')}")