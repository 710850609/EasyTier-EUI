#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理脚本
"""

import os
import re
import sys
import time
import signal
import subprocess
import logging
from pathlib import Path
import psutil


def strip_ansi(text):
    """去除 ANSI 转义序列"""
    ansi_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_pattern.sub('', text)

class ProcessManager:

    def __init__(self, pid_file: str) -> None:
        self.pid_file = Path(pid_file)
        pass


    def __check_process(self, pid: int) -> bool:
        return psutil.pid_exists(pid)

    def status(self) -> bool:
        """
        检查应用状态
        返回: True=运行中, False=未运行
        """
        if self.pid_file.exists():
            try:
                pid = int(self.pid_file.read_text().strip().split()[0])
                if self.__check_process(pid):
                    return True
                else:
                    # 进程不在运行但 pidfile 存在 - 清理
                    self.pid_file.unlink(missing_ok=True)
            except (ValueError, IndexError):
                self.pid_file.unlink(missing_ok=True)
        
        return False


    def start(self, start_cmd:str) -> int:
        """
        启动进程
        """
        if self.status():
            logging.info("Process already running")
            return 0
        
        logging.info("Starting process ...")
        # 确保目录存在
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 启动进程: bash -c "${CMD}" >> /dev/null 2>&1 & (Linux/macOS)
        # 使用 Popen 实现后台运行，不依赖当前 Python 进程
        try:
            # 根据平台选择启动方式
            if sys.platform == 'win32':
                # 在命令中添加 --no-color
                # if '--no-color' not in self.start_cmd:
                #     self.start_cmd += ' --no-color'
                # Windows: 直接使用命令，创建新进程组
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE  # <-- 关键：强制隐藏窗口
                process = subprocess.Popen(
                    start_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                    startupinfo=startupinfo,
                )
            else:
                # Linux/macOS: 使用 bash -c
                process = subprocess.Popen(
                    ["bash", "-c", start_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    encoding='utf-8',
                    errors='replace',
                    start_new_session=True,  # 等效于 & 后台运行，脱离终端
                )

            # 等待一小段时间检查进程是否立即失败
            import time
            time.sleep(2)

            # 检查进程是否还在运行
            if process.poll() is not None:
                # 进程已退出，读取错误信息
                _, stderr = process.communicate()
                error_msg = stderr
                if isinstance(error_msg, bytes):
                    error_msg = stderr.decode('utf-8', errors='ignore').srip() if stderr else "未知错误"

                error_msg = strip_ansi(error_msg)
                raise RuntimeError(f"{error_msg}")

            pid = process.pid

            # 写入 PID 文件（等效于 printf "%s" "$!" > ${self.pid_file}）
            self.pid_file.write_text(str(pid))

            logging.info(f"Started with PID: {pid}")
            return 0

        except Exception as e:
            logging.error(f"Failed to start: {e}")
            raise RuntimeError(f"启动进程失败: {e}") from e


    def stop(self) -> int:
        """
        停止进程
        """
        logging.info("Stopping process ...")
        
        # 检查 PID 文件是否可读
        if not self.pid_file.exists() or not os.access(self.pid_file, os.R_OK):
            logging.info("PID file not found or not readable")
            return 0
        
        # 读取 PID（等效于 head -n 1 "${self.pid_file}" | tr -d '[:space:]'）
        try:
            pid = int(self.pid_file.read_text().strip().split()[0])
        except (ValueError, IndexError) as e:
            logging.info(f"Invalid PID file: {e}")
            self.pid_file.unlink(missing_ok=True)
            return 0
        
        logging.info(f"pid={pid}")
        
        # 检查进程是否存在
        if not self.__check_process(pid):
            # 进程不存在，删除 pidfile
            self.pid_file.unlink(missing_ok=True)
            logging.info("remove pid file 1")
            return 0
        
        # 发送终止信号
        logging.info(f"send TERM signal to PID:{pid}...")
        try:
            if sys.platform == 'win32':
                # Windows: 使用 taskkill 发送信号

                subprocess.run(['taskkill', '/PID', str(pid)], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW) # 禁止创建窗口
            else:
                # Linux/macOS: 使用 SIGTERM
                os.kill(pid, signal.SIGTERM)
        except OSError as e:
            logging.info(f"Failed to send TERM: {e}")
            return 1
        
        # 等待进程退出（最多 10 秒）
        count = 0
        while self.__check_process(pid) and count < 5:
            time.sleep(1)
            count += 1
            logging.info(f"waiting process terminal... ({count}s/5s)")
        
        # 如果还在，强制终止
        if self.__check_process(pid):
            logging.info(f"send KILL signal to PID:{pid}...")
            try:
                if sys.platform == 'win32':
                    # Windows: 使用 taskkill /F 强制终止
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW) # 禁止创建窗口
                else:
                    # Linux/macOS: 使用 SIGKILL
                    os.kill(pid, signal.SIGKILL)
            except OSError as e:
                logging.info(f"Failed to send KILL: {e}")
            
            time.sleep(1)
            self.pid_file.unlink(missing_ok=True)
        else:
            logging.info("process killed... ")
            self.pid_file.unlink(missing_ok=True)
        
        return 0