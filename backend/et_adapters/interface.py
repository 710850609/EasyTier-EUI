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
    def get_peers(self, instance_name: str, relay_path: bool = False, proxy_info: bool = True) -> list[dict]:
        """Collect network information for a specific instance."""

    @abstractmethod
    def change_log_level(self, log_level: str, **kwargs) -> None:
        """Change log level."""

    @abstractmethod
    def get_logs(self, params: dict) -> dict:
        """Get logs.
        Returns {'lines': str, 'offset': int, 'appending': bool}
        """

    @abstractmethod
    def check_peers(self, peer_uris: list[str], max_wait_second: int = 6) -> dict:
        """Check if public peer URIs are reachable (standalone check, does not affect running instances).

        :param peer_uris: list of peer URIs to check, e.g. ['tcp://1.2.3.4:11010', ...]
        :param max_wait_second: maximum wait time in seconds
        :return: {'success': {uri: {relay, latency, hostname, ...}}, 'fail': [uri, ...]}
        """