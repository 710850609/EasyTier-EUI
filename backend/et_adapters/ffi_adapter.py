#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FfiAdapter — current default FFI adapter for v2.4.5/v2.6.4"""

import ctypes, json, logging, os, platform, re, threading, time
from ctypes import c_char_p, c_int, c_void_p, POINTER, Structure, c_size_t
from pathlib import Path
from typing import Dict, Any, List, Optional

from .interface import IEasyTierAdapter
from .models import NetworkInstanceInfo

logger = logging.getLogger(__name__)


class KeyValuePair(Structure):
    _fields_ = [("key", c_void_p), ("value", c_void_p)]


class FfiAdapter(IEasyTierAdapter):

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

    def __init__(self):
        self._lib = None
        self._lock = threading.RLock()
        self._so_path: Optional[str] = None
        self._load_library()

    def _load_library(self):
        lib_name = "libeasytier_ffi.so"
        lib_paths = [
            Path(__file__).parent.parent / lib_name,
            Path(os.environ.get('EUI_LIB_DIR', '')) / lib_name,
        ]
        arch = platform.machine()
        if arch == 'aarch64':
            lib_paths.append(Path(__file__).parent.parent / 'arm64-v8a' / lib_name)
        elif arch == 'armv7l':
            lib_paths.append(Path(__file__).parent.parent / 'armeabi-v7a' / lib_name)

        system_path = self._find_system_lib_path(lib_name)
        if system_path:
            lib_paths.append(Path(system_path))

        for lib_path in lib_paths:
            if lib_path.exists():
                try:
                    self._lib = ctypes.CDLL(str(lib_path))
                    self._setup_functions()
                    self._so_path = str(lib_path)
                    logger.info(f"Loaded EasyTier FFI: {self._so_path}")
                    return
                except OSError as e:
                    logger.warning(f"Failed to load {lib_path}: {e}")

        try:
            self._lib = ctypes.CDLL(lib_name)
            self._setup_functions()
            logger.info("Loaded EasyTier FFI via system library path")
        except OSError as e:
            logger.warning(f"Failed to load via system path: {e}")

    def _find_system_lib_path(self, lib_name: str) -> Optional[str]:
        try:
            with open('/proc/self/maps', 'r') as f:
                for line in f:
                    if lib_name in line:
                        path = line.rsplit(' ', 1)[-1].strip()
                        logger.debug(f"_find_system_lib_path found candidate: {path}")
                        if os.path.isfile(path):
                            return path
                        else:
                            logger.debug(f"_find_system_lib_path isfile=False: {path}")
            logger.debug(f"_find_system_lib_path: {lib_name} not found in /proc/self/maps")
        except Exception as e:
            logger.warning(f"_find_system_lib_path failed: {e}")
        return None

    def _has_symbol(self, name: str) -> bool:
        if self._lib is None:
            return False
        try:
            getattr(self._lib, name)
            return True
        except AttributeError:
            return False

    def is_available(self) -> bool:
        if self._lib is None:
            return False
        return (all(self._has_symbol(s) for s in self.REQUIRED_SYMBOLS) and
                all(not self._has_symbol(s) for s in self.MISSING_SYMBOLS))

    def _setup_functions(self):
        lib = self._lib
        if self._has_symbol('parse_config'):
            lib.parse_config.argtypes = [c_char_p]
            lib.parse_config.restype = c_int
        if self._has_symbol('run_network_instance'):
            lib.run_network_instance.argtypes = [c_char_p]
            lib.run_network_instance.restype = c_int
        if self._has_symbol('retain_network_instance'):
            lib.retain_network_instance.argtypes = [POINTER(c_char_p), c_size_t]
            lib.retain_network_instance.restype = c_int
        if self._has_symbol('collect_network_infos'):
            lib.collect_network_infos.argtypes = [POINTER(KeyValuePair), c_size_t]
            lib.collect_network_infos.restype = c_int
        if self._has_symbol('set_tun_fd'):
            lib.set_tun_fd.argtypes = [c_char_p, c_int]
            lib.set_tun_fd.restype = c_int
        if self._has_symbol('get_error_msg'):
            lib.get_error_msg.argtypes = [POINTER(c_char_p)]
            lib.get_error_msg.restype = None
        if self._has_symbol('free_string'):
            lib.free_string.argtypes = [c_void_p]
            lib.free_string.restype = None

    def start_network(self, toml_path: str, instance_name: str) -> None:
        if self._lib is None:
            raise RuntimeError("FFI library not loaded")
        try:
            import tomlkit
            with open(toml_path, 'r', encoding='utf-8') as f:
                toml_config = f.read()
            doc = tomlkit.parse(toml_config)
            flags = doc.get('flags', {})
            if 'compression' in flags:
                compression = flags['compression']
                if compression:
                    flags['data_compress_algo'] = compression.capitalize()
                del flags['compression']
                doc['flags'] = flags
                toml_config = tomlkit.dumps(doc)
            ret = self.parse_config(toml_config)
            if ret != 0:
                raise RuntimeError(f"Config parse failed: {self.get_last_error()}")
            with self._lock:
                ret = self._lib.run_network_instance(toml_config.encode('utf-8'))
                if ret != 0:
                    raise RuntimeError(f"run_network_instance failed: {self.get_last_error()}")
            time.sleep(1.0)
            logger.info(f"Instance '{instance_name}' started via FFI")
        except Exception as e:
            logger.exception(f"start_network failed: {e}")
            raise

    def parse_config(self, toml_config: str) -> int:
        if self._lib is None or not self._has_symbol('parse_config'):
            return -1
        try:
            with self._lock:
                return self._lib.parse_config(toml_config.encode('utf-8'))
        except Exception as e:
            logger.exception(f"parse_config failed: {e}")
            return -1

    def set_tun_fd(self, instance_name: str, fd: int) -> int:
        if self._lib is None:
            raise RuntimeError("FFI library not loaded")
        if not self._has_symbol('set_tun_fd'):
            raise RuntimeError("set_tun_fd symbol not available")
        try:
            with self._lock:
                ret = self._lib.set_tun_fd(instance_name.encode('utf-8'), fd)
                if ret != 0:
                    raise RuntimeError(f"set_tun_fd failed: {self.get_last_error()}")
                return 0
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"set_tun_fd failed: {e}") from e

    def stop_network(self, instance_name: str = None) -> None:
        if instance_name is None:
            self._retain_instances([])
        else:
            all_instances = self._list_all_instance_names()
            keep = [n for n in all_instances if n != instance_name]
            self._retain_instances(keep)

    def _retain_instances(self, names: List[str]) -> None:
        if self._lib is None:
            raise RuntimeError("FFI library not loaded")
        try:
            with self._lock:
                if not names:
                    ret = self._lib.retain_network_instance(None, 0)
                else:
                    encoded = [n.encode('utf-8') for n in names]
                    arr = (c_char_p * len(names))(*encoded)
                    ret = self._lib.retain_network_instance(arr, len(names))
                if ret != 0:
                    raise RuntimeError(f"retain_network_instance failed: {self.get_last_error()}")
        except Exception as e:
            logger.exception(f"_retain_instances failed: {e}")
            raise

    def _list_all_instance_names(self) -> List[str]:
        info = self._collect_via_raw_ffi(20)
        return list(info.keys())

    def get_last_error(self) -> str:
        if self._lib is None or not self._has_symbol('get_error_msg'):
            return ""
        try:
            with self._lock:
                error_ptr = c_char_p()
                self._lib.get_error_msg(ctypes.byref(error_ptr))
            raw_ptr = ctypes.cast(error_ptr, c_void_p).value
            if raw_ptr:
                msg = ctypes.string_at(raw_ptr).decode('utf-8', errors='replace')
                if self._has_symbol('free_string'):
                    self._lib.free_string(raw_ptr)
                return msg
            return ""
        except Exception:
            return ""

    def _collect_via_raw_ffi(self, max_len: int) -> Dict[str, Any]:
        if self._lib is None or not self._has_symbol('collect_network_infos'):
            return {}
        for attempt in range(3):
            try:
                with self._lock:
                    infos = (KeyValuePair * max_len)()
                    count = self._lib.collect_network_infos(infos, max_len)
                    if count < 0:
                        if attempt < 2:
                            time.sleep(0.5)
                            continue
                        return {}
                    result = {}
                    for i in range(min(count, max_len)):
                        key_ptr = infos[i].key
                        val_ptr = infos[i].value
                        key = ctypes.string_at(key_ptr).decode('utf-8') if key_ptr else ""
                        value = ctypes.string_at(val_ptr).decode('utf-8') if val_ptr else ""
                        logger.debug(f"collect_network_infos: key={key}, value={value}")
                        result[key] = json.loads(value) if value else {}
                        if self._has_symbol('free_string'):
                            if key_ptr:
                                self._lib.free_string(key_ptr)
                            if val_ptr:
                                self._lib.free_string(val_ptr)
                    return result
            except Exception as e:
                logger.exception(f"_collect_via_raw_ffi attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(0.5)
        return {}

    def get_version(self) -> str:
        if self._so_path and os.path.isfile(self._so_path):
            try:
                with open(self._so_path, 'rb') as f:
                    data = f.read()
                match = re.search(rb'(\d+\.\d+\.\d+(-[a-f0-9]{7,8})?)', data)
                if match:
                    return match.group(1).decode()
                else:
                    logger.warning(f"Version pattern not found in binary: {self._so_path}")
            except Exception as e:
                logger.warning(f"Failed to scan binary for version: {e}")
        else:
            logger.debug(f"No so_path available for version scan: {self._so_path}")
        try:
            raw = self._collect_via_raw_ffi(1)
            for instance_data in raw.values():
                for pair in instance_data.get('peer_route_pairs') or []:
                    route = pair.get('route') or {}
                    ver = route.get('version', '')
                    if ver:
                        return ver
        except Exception as e:
            logger.warning(f"Failed to get version from network data: {e}")
        return "unknown"

    def get_network_infos(self, max_length: int = 10) -> Dict[str, NetworkInstanceInfo]:
        raw = self._collect_via_raw_ffi(max_length)
        if not raw:
            return {}

        result = {}
        for instance_name, json_data in raw.items():
            result[instance_name] = NetworkInstanceInfo.from_dict(json_data) if json_data else NetworkInstanceInfo()
        return result

    def get_network_infos_raw(self, max_length: int = 10) -> Dict[str, Any]:
        return self._collect_via_raw_ffi(max_length)