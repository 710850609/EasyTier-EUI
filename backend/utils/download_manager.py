#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import threading
import uuid
from pathlib import Path

from utils import run_configs


class DownloadTask:
    STATUS_RUNNING = 0
    STATUS_SUCCESS = 1
    STATUS_FAILED = 2

    def __init__(self, download_id: str, params: dict):
        self.download_id = download_id
        self.params = params
        self.total_progress = 100
        self.current_progress = 0
        self.description = '准备下载...'
        self.status = self.STATUS_RUNNING
        self.file_path = None
        self.file_name = None
        self._lock = threading.Lock()

    def update_progress(self, current: int, description: str = None, total: int = None):
        with self._lock:
            self.current_progress = current
            if total is not None:
                self.total_progress = total
            if description:
                self.description = description
            self._save()

    def set_completed(self, file_path: str, file_name: str):
        with self._lock:
            self.status = self.STATUS_SUCCESS
            self.current_progress = self.total_progress
            self.file_path = file_path
            self.file_name = file_name
            self.description = f'{file_name} 已完成准备'
            self._save()

    def set_error(self, error: str):
        with self._lock:
            self.status = self.STATUS_FAILED
            self.description = f'下载失败: {error}'
            self._save()

    def _save(self):
        status_file = self._status_file_path()
        data = {
            'download_id': self.download_id,
            'total_progress': self.total_progress,
            'current_progress': self.current_progress,
            'description': self.description,
            'status': self.status,
            'file_path': self.file_path,
            'file_name': self.file_name,
        }
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def _status_file_path(self) -> str:
        return os.path.join(run_configs.data_dir(), 'download', 'tasks', f'{self.download_id}.json')

    def to_dict(self) -> dict:
        return {
            'download_id': self.download_id,
            'total_progress': self.total_progress,
            'current_progress': self.current_progress,
            'description': self.description,
            'status': self.status,
            'file_path': self.file_path,
            'file_name': self.file_name,
        }

    @staticmethod
    def load(download_id: str) -> dict:
        status_file = os.path.join(run_configs.data_dir(), 'download', 'tasks', f'{download_id}.json')
        if not os.path.exists(status_file):
            return None
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return None
                return json.loads(content)
        except (json.JSONDecodeError, IOError):
            return None


def new_download_id() -> str:
    return uuid.uuid4().hex[:12]


def run_async_download(target_func, task: DownloadTask, *args):
    def _run():
        try:
            target_func(task, *args)
        except Exception as e:
            logging.exception(f'异步下载任务失败: {task.download_id}')
            task.set_error(str(e))

    if hasattr(os, 'fork'):
        # Unix/CGI 模式：fork 子进程执行下载，父进程立即返回
        # 避免 CGI 进程退出时 daemon 线程被强制终止
        pid = os.fork()
        if pid == 0:
            # 子进程：关闭继承的 CGI stdio，避免 web server 等待管道关闭
            os.closerange(0, 3)
            devnull = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull, 0)
            os.dup2(devnull, 1)
            os.dup2(devnull, 2)
            os.close(devnull)
            # 执行下载任务
            try:
                _run()
            finally:
                os._exit(0)
        # 父进程：立即返回
    else:
        # Windows/HTTP Server 模式：使用 daemon 线程
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
    return task