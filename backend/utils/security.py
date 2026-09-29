#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具模块 - 防止路径遍历、注入攻击
"""
import re
import logging
from typing import Optional

from locales import get_message

logger = logging.getLogger(__name__)
# 禁止的字符模式，用于防止各种注入
DANGEROUS_PATTERNS = [
    r'/',  # 路径分隔符
    r'\\',  # 路径分隔符（Windows）
    r';',  # 命令分隔符
    r'&',  # 后台命令
    r'\|',  # 管道
    r'`',  # 命令替换
    r'\$\(',  # 命令替换
    r'>',  # 重定向
    r'<',  # 重定向
    r'[\r\n]',  # 换行符
]


def sanitize_filename(filename: str) -> Optional[str]:
    """
    清理文件名
    
    Args:
        filename: 输入文件名
        
    Returns:
        安全的文件名，或 None 如果不安全
    """
    if not filename:
        return None
    
    # 检查危险模式
    for pattern in DANGEROUS_PATTERNS:
        m = re.search(pattern, filename)
        if m:
            msg = get_message('error.dangerous_filename', filename=filename, character=repr(m.group()))
            logger.warning(msg)
            raise ValueError(msg)
    
    return filename


def validate_profile(profile: Optional[str]) -> Optional[str]:
    """
    验证配置文件名
    
    Args:
        profile: 配置文件名
        
    Returns:
        清理后的文件名，或 None 如果不安全
    """
    if not profile:
        return None
    
    # 清理文件名（危险字符会抛出 ValueError）
    clean_name = sanitize_filename(profile)

    # 确保是 .toml 结尾
    if not clean_name.endswith('.toml'):
        clean_name += '.toml'
    
    return clean_name