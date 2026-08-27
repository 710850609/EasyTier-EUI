#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EasyTier adapter abstract interface"""

from abc import ABC, abstractmethod


class IEasyTierAdapter(ABC):

    @abstractmethod
    def get_version(self) -> str:
        """Get the EasyTier version string."""

    @abstractmethod
    def start_network(self, toml_path: str, instance_name: str) -> None:
        """Start a network instance from a TOML config file path. Raises on error."""

    @abstractmethod
    def stop_network(self, instance_name: str) -> None:
        """ Stop network instance(s). Raises on error. """

    @abstractmethod
    def status(self, instance_name: str) -> bool:
        """Check if a network instance is running."""

    @abstractmethod
    def get_peers(self, instance_name: str, relay_path: bool = False) -> list[dict]:
        """Collect network information for a specific instance."""

    @abstractmethod
    def change_log_level(self, log_level: str, **kwargs) -> None:
        """Change log level."""