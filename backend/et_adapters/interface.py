#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTier adapter abstract interface"""

from abc import ABC, abstractmethod
from typing import Dict

from .models import NetworkInstanceInfo


class IEasyTierAdapter(ABC):

    @abstractmethod
    def start_network(self, toml_path: str, instance_name: str) -> None:
        """Start a network instance from a TOML config file path. Raises on error."""

    @abstractmethod
    def stop_network(self, instance_name: str = None) -> None:
        """
        Stop network instance(s). Raises on error.
        If instance_name is None, stops all instances.
        """

    @abstractmethod
    def get_network_infos(self, max_length: int = 10) -> Dict[str, NetworkInstanceInfo]:
        """Collect network information keyed by instance name."""

    @abstractmethod
    def get_version(self) -> str:
        """Get the EasyTier version string."""