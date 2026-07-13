#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import threading
import uuid
from typing import Optional

from locales import get_message
from utils import run_configs


class AsyncTask:
    STATUS_RUNNING = 0
    STATUS_SUCCESS = 1
    STATUS_FAILED = 2

    def __init__(self, params: dict, task_type: str, init_description: str, error_prefix: str, task_id: str = None):
        self.task_id = task_id or self.generate_id()
        self.params = params
        self._task_type = task_type
        self._error_prefix = error_prefix
        self.total_progress = 100
        self.current_progress = 0
        self.description = init_description
        self.status = self.STATUS_RUNNING
        self._lock = threading.Lock()

    @staticmethod
    def generate_id() -> str:
        return uuid.uuid4().hex[:12]

    def update_progress(self, current: int, description: str = None, total: int = None):
        with self._lock:
            self.current_progress = current
            if total is not None:
                self.total_progress = total
            if description:
                self.description = description
            self._save()

    def set_completed(self, description: str = None):
        with self._lock:
            self.status = self.STATUS_SUCCESS
            self.current_progress = self.total_progress
            if description:
                self.description = description
            self._save()

    def set_error(self, error: str):
        with self._lock:
            self.status = self.STATUS_FAILED
            self.description = f'{self._error_prefix}: {error}'
            self._save()

    def start(self, target_func, *args):
        from locales import get_lang, set_lang
        current_lang = get_lang()
        def _run():
            set_lang(current_lang)
            try:
                target_func(self, *args)
            except Exception as e:
                logging.exception(f'异步任务失败: {self.task_id}')
                self.set_error(str(e))

        if hasattr(os, 'fork'):
            pid = os.fork()
            if pid == 0:
                os.closerange(0, 3)
                devnull = os.open(os.devnull, os.O_RDWR)
                os.dup2(devnull, 0)
                os.dup2(devnull, 1)
                os.dup2(devnull, 2)
                os.close(devnull)
                try:
                    _run()
                finally:
                    os._exit(0)
        else:
            thread = threading.Thread(target=_run, daemon=True)
            thread.start()
        return self

    def _build_save_data(self) -> dict:
        return {
            'task_id': self.task_id,
            'total_progress': self.total_progress,
            'current_progress': self.current_progress,
            'description': self.description,
            'status': self.status,
        }

    def _save(self):
        status_file = self._status_file_path()
        data = self._build_save_data()
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def _status_file_path(self) -> str:
        return os.path.join(run_configs.data_dir(), 'tasks', self._task_type, f'{self.task_id}.json')

    def to_dict(self) -> dict:
        return self._build_save_data()

    @staticmethod
    def load(task_id: str, task_type: str) -> Optional[dict]:
        status_file = os.path.join(run_configs.data_dir(), 'tasks', task_type, f'{task_id}.json')
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


class DownloadTask(AsyncTask):
    def __init__(self, params: dict, download_id: str = None):
        super().__init__(params, 'download', get_message('task.preparing_download'), get_message('task.download_failed'), download_id)
        self.download_id = self.task_id
        self.file_path = None
        self.file_name = None

    def set_completed(self, file_path: str, file_name: str):
        self.file_path = file_path
        self.file_name = file_name
        super().set_completed(get_message('task.download_ready', file_name=file_name))

    def _build_save_data(self) -> dict:
        data = super()._build_save_data()
        data['download_id'] = self.download_id
        data['file_path'] = self.file_path
        data['file_name'] = self.file_name
        return data

    @staticmethod
    def load(download_id: str) -> Optional[dict]:
        return AsyncTask.load(download_id, 'download')


class UpdateTask(AsyncTask):
    def __init__(self, params: dict, update_id: str = None):
        super().__init__(params, 'update', get_message('task.preparing_update'), get_message('task.update_failed'), update_id)
        self.update_id = self.task_id
        self.update_version = ''

    def set_update_version(self, update_version: str):
        self.update_version = update_version

    def _build_save_data(self) -> dict:
        data = super()._build_save_data()
        data['update_id'] = self.update_id
        data['update_version'] = self.update_version
        return data

    @staticmethod
    def load(update_id: str) -> Optional[dict]:
        return AsyncTask.load(update_id, 'update')