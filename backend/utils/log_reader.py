#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LogFileReader:
    """日志文件读取工具 — 无状态，支持首次 tail 读取 + 增量 offset 读取"""

    @staticmethod
    def read(log_file: Path, max_lines: int = 100, max_bytes: int = 128 * 1024, offset: int = 0) -> dict:
        if not log_file.exists():
            return {'lines': '', 'offset': 0, 'appending': False}

        try:
            file_size = log_file.stat().st_size

            if 0 < offset <= file_size:
                return LogFileReader._read_incremental(log_file, offset, max_bytes)

            lines = LogFileReader._tail_lines(log_file, max_lines, max_bytes)
            return {
                'lines': ''.join(lines),
                'offset': file_size,
                'appending': False
            }

        except (OSError, PermissionError) as e:
            logger.warning(f"读取日志文件失败: {log_file} - {e}")
            return {'lines': '', 'offset': 0, 'appending': False}

    @staticmethod
    def _read_incremental(log_file: Path, offset: int, max_bytes: int) -> dict:
        file_size = log_file.stat().st_size
        with open(log_file, 'rb') as f:
            f.seek(offset)
            raw = f.read(max_bytes)

        if not raw:
            return {'lines': '', 'offset': offset, 'appending': True}

        text = raw.decode('utf-8', errors='replace')
        return {
            'lines': text,
            'offset': min(file_size, offset + len(raw)),
            'appending': True
        }

    @staticmethod
    def _tail_lines(log_file: Path, max_lines: int, max_bytes: int) -> list:
        BLOCK_SIZE = 4096

        with open(log_file, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            if file_size == 0:
                return []

            pos = file_size
            blocks = []
            lines_found = 0
            total_bytes = 0

            while pos > 0 and lines_found < max_lines and total_bytes < max_bytes:
                read_size = min(BLOCK_SIZE, pos)
                pos -= read_size
                f.seek(pos)
                block = f.read(read_size)
                blocks.insert(0, block)
                total_bytes += read_size
                lines_found += block.count(b'\n')

            raw = b''.join(blocks)
            text = raw.decode('utf-8', errors='replace')

            if pos > 0:
                first_nl = text.find('\n')
                if first_nl >= 0:
                    text = text[first_nl + 1:]

            lines = text.splitlines(True)
            return lines[-max_lines:] if len(lines) > max_lines else lines