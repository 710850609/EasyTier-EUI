#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FfiMainAdapter — reserved for future main-branch FFI development"""

from typing import List

from .ffi_adapter import FfiAdapter


class FfiMainAdapter(FfiAdapter):
    """
    Reserved for future main-branch FFI development.

    Currently identical to FfiAdapter. When new symbols are added to the main
    branch FFI, update REQUIRED_SYMBOLS and MISSING_SYMBOLS to differentiate.
    """

    REQUIRED_SYMBOLS = [
        'parse_config',
        'run_network_instance',
        'retain_network_instance',
        'collect_network_infos',
        'set_tun_fd',
        'get_error_msg',
        'free_string',
    ]
    MISSING_SYMBOLS: List[str] = []