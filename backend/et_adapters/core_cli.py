#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CoreCliAdapter — CLI subprocess adapter for EasyTier Core"""

import json
import logging
import os
import subprocess
from typing import Any, Dict, Optional

from utils import run_configs
from .interface import IEasyTierAdapter
from .models import NetworkInstanceInfo

logger = logging.getLogger(__name__)


class CoreCliAdapter(IEasyTierAdapter):

    def __init__(self):
        self._cli_path: Optional[str] = None
        self._detect_cli()

    def _detect_cli(self):
        candidates = [
            os.path.join(run_configs.core_dir(), 'easytier-cli'),
            os.path.join(run_configs.core_dir(), 'easytier-core'),
            '/usr/bin/easytier-cli',
            '/usr/local/bin/easytier-cli',
        ]
        for path in candidates:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                self._cli_path = path
                logger.info(f"CoreCliAdapter using: {path}")
                return
        logger.warning("No easytier-cli found")

    def is_available(self) -> bool:
        return self._cli_path is not None

    def start_network(self, toml_path: str, instance_name: str) -> None:
        if not self._cli_path:
            raise RuntimeError("CLI path not found")
        try:
            proc = subprocess.Popen(
                [self._cli_path, '--config', toml_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Instance '{instance_name}' started via CLI (PID: {proc.pid})")
        except Exception as e:
            logger.exception(f"start_network failed: {e}")
            raise

    def stop_network(self, instance_name: str = None) -> None:
        if not self._cli_path:
            raise RuntimeError("CLI path not found")
        try:
            cmd = [self._cli_path, 'instance', 'stop']
            if instance_name:
                cmd.extend(['--name', instance_name])
            else:
                cmd.append('--all')
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"CLI stop failed: {result.stderr.strip()}")
        except Exception as e:
            logger.exception(f"stop_network failed: {e}")
            raise

    def get_network_infos(self, max_length: int = 10) -> Dict[str, NetworkInstanceInfo]:
        if not self._cli_path:
            return {}
        try:
            cmd = [self._cli_path, 'node', 'list', '--format', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return {}
            data = json.loads(result.stdout)
            instances = data if isinstance(data, list) else [data]
            info = {}
            for instance in instances[:max_length]:
                name = instance.get('instance_name', 'default')
                info[name] = NetworkInstanceInfo.from_dict(instance)
            return info
        except Exception as e:
            logger.exception(f"get_network_infos failed: {e}")
            return {}

    def get_network_infos_raw(self, max_length: int = 10) -> Dict[str, Any]:
        if not self._cli_path:
            return {}
        try:
            cmd = [self._cli_path, 'node', 'list', '--format', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return {}
            data = json.loads(result.stdout)
            instances = data if isinstance(data, list) else [data]
            info = {}
            for instance in instances[:max_length]:
                name = instance.get('instance_name', 'default')
                info[name] = instance
            return info
        except Exception as e:
            logger.exception(f"get_network_infos_raw failed: {e}")
            return {}

    def get_version(self) -> str:
        if not self._cli_path:
            return "unknown"
        try:
            result = subprocess.run(
                [self._cli_path, '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except Exception:
            return "unknown"

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        raise NotImplementedError("CoreCliAdapter does not support set_tun_fd")