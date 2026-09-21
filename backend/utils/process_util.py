#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理脚本
"""

import os
import re
import shlex
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path

from utils import run_configs

try:
    import psutil
except ImportError:
    psutil = None


_ANSI_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def pid_exists(pid):
    """
    通过检查 /proc/[pid] 目录是否运行
    """
    if pid <= 0:
        return False
    if psutil is not None:
        return psutil.pid_exists(pid)
    if run_configs.IS_ANDROID:
        try:
            # 检查进程目录是否存在且可访问
            return os.path.exists(f"/proc/{pid}")
        except Exception:
            # 发生任何异常，都认为进程不存在或无法访问
            return False
    else:
        return False

def get_cmdline(pid: int) -> list[str]:
    """
    获取进程命令行参数列表（Android 兼容）
    返回: 命令行参数列表，如 ['python', 'main.py', '--port', '8080']
    """
    try:
        if run_configs.IS_ANDROID or psutil is None:
            # Android 或 psutil 不可用时，直接读取 /proc/[pid]/cmdline
            with open(f"/proc/{pid}/cmdline", "r") as f:
                return f.read().split("\x00")
        else:
            p = psutil.Process(pid)
            return p.cmdline()
    except Exception as e:
        logging.warning(f"Failed to read cmdline for PID {pid}: {e}")
        return []


def strip_ansi(text):
    """去除 ANSI 转义序列"""
    return _ANSI_PATTERN.sub('', text)

class ProcessManager:

    def __init__(self, pid_file: str = None) -> None:
        self.pid_file = Path(pid_file) if pid_file else None
        self._process = None


    def __check_process(self, pid: int) -> bool:
        if psutil is not None:
            return psutil.pid_exists(pid)
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def status(self) -> bool:
        """
        检查应用状态
        返回: True=运行中, False=未运行
        """
        if self._process is not None:
            return self._process.poll() is None
        if self.pid_file is None:
            return False
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip().split()[0])
                if self.__check_process(pid):
                    return True
                else:
                    self.pid_file.unlink(missing_ok=True)
            except (ValueError, IndexError):
                self.pid_file.unlink(missing_ok=True)
        return False


    def start(self, start_cmd:list[str], wait_seconds: float = 2, raise_on_failure: bool = True) -> None:
        """
        启动进程，失败时根据 raise_on_failure 决定抛异常或静默返回
        :param start_cmd: 启动命令列表
        :param wait_seconds: 启动后等待秒数
        :param raise_on_failure: 启动失败时是否抛出 RuntimeError
        """
        if self.status():
            logging.info("Process already running")
            return
        
        logging.info("Starting process ...")
        if self.pid_file is not None:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 根据平台选择启动方式
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                self._process = subprocess.Popen(
                    start_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE if raise_on_failure else subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
                    startupinfo=startupinfo,
                )
            else:
                bash_cmd = ["sh", "-c", "exec " + " ".join(shlex.quote(x) for x in start_cmd)]
                self._process = subprocess.Popen(
                    bash_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE if raise_on_failure else subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    encoding='utf-8',
                    errors='replace',
                    start_new_session=True,
                )

            time.sleep(wait_seconds)

            if self._process.poll() is not None:
                process = self._process
                self._process = None
                if raise_on_failure:
                    _, stderr_data = process.communicate()
                    error_msg = stderr_data
                    if isinstance(error_msg, bytes):
                        error_msg = stderr_data.decode('utf-8', errors='ignore').strip() if stderr_data else "未知错误"
                    error_msg = strip_ansi(error_msg)
                    raise RuntimeError(f"{error_msg}")
                return

            pid = self._process.pid

            if self.pid_file is not None:
                self.pid_file.write_text(str(pid))

            logging.info(f"Started with PID: {pid}")

        except RuntimeError as e:
            raise e
        except Exception as e:
            self._process = None
            if raise_on_failure:
                raise RuntimeError(f"Failed to start: {e}") from e
            raise


    def stop(self, timeout: int = 5) -> int:
        """
        停止进程：
        1. 优先从 Popen 句柄获取 PID
        2. 回退到 PID 文件
        3. 执行 _kill_pid（含 pid_file 清理）
        """
        logging.info("Stopping process ...")

        pid = None

        # 1. 尝试从 Popen 句柄获取 PID
        if self._process is not None:
            if self._process.poll() is not None:
                self._process = None
                return 0
            pid = self._process.pid
            logging.info(f"Stopping by handle, pid={pid}")

        # 2. 回退到 PID 文件
        if pid is None and self.pid_file is not None:
            try:
                if self.pid_file.exists() and os.access(self.pid_file, os.R_OK):
                    pid = int(self.pid_file.read_text().strip().split()[0])
                    logging.info(f"pid={pid}")
            except (ValueError, IndexError) as e:
                logging.info(f"Invalid PID file: {e}")
                self.pid_file.unlink(missing_ok=True)
                return 0

        if pid is None:
            logging.info("No PID found")
            return 0

        # 3. 执行杀逻辑（_kill_pid 内统一清理 pid_file）
        self._kill_pid(pid, timeout)
        if self._process is not None:
            self._process.wait(timeout=2)
            self._process = None
        return 0

    def _kill_pid(self, pid: int, timeout: int = 5) -> int:
        """通过 PID 停止进程（保留原有逻辑）"""
        logging.info(f"send TERM signal to PID:{pid}...")
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/T', '/PID', str(pid)], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    os.kill(pid, signal.SIGTERM)
        except OSError as e:
            logging.info(f"Failed to send TERM: {e}")
            if self.pid_file is not None:
                self.pid_file.unlink(missing_ok=True)
            return 1

        count = 0
        while self.__check_process(pid) and count < timeout:
            time.sleep(1)
            count += 1
            logging.info(f"waiting process terminal... ({count}s/{timeout}s)")

        if self.__check_process(pid):
            logging.info(f"send KILL signal to PID:{pid}...")
            try:
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    try:
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                    except (ProcessLookupError, OSError):
                        os.kill(pid, signal.SIGKILL)
            except OSError as e:
                logging.info(f"Failed to send KILL: {e}")

            time.sleep(1)
            self.pid_file.unlink(missing_ok=True)
        else:
            logging.info("process killed... ")
            self.pid_file.unlink(missing_ok=True)

        return 0