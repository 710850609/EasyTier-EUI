#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具模块 - 防止路径遍历、注入攻击
"""
import os
import re
import logging
from typing import Optional

# 禁止的字符模式，用于防止各种注入
DANGEROUS_PATTERNS = [
    r'\.\./',  # 路径遍历
    r'\.\.\\',  # Windows 路径遍历
    r';',  # 命令分隔符
    r'&',  # 后台命令
    r'\|',  # 管道
    r'`',  # 命令替换
    r'\$\(',  # 命令替换
    r'>',  # 重定向
    r'<',  # 重定向
    r'\\',  # 反斜杠，潜在转义
    r'[\r\n]',  # 换行符
]

# 安全的文件名正则（允许字母、数字、中文汉字、下划线、点、连字符）
SAFE_FILENAME_REGEX = re.compile(r'^[a-zA-Z0-9\u4e00-\u9fff_\.\-]+$')


def sanitize_path(path: str, base_dir: str) -> Optional[str]:
    """
    清理路径，防止路径遍历攻击
    
    Args:
        path: 输入路径
        base_dir: 允许访问的基础目录
        
    Returns:
        安全的绝对路径，或 None 如果不安全
    """
    if not path:
        return None
    
    # 检查路径遍历特征
    if '..' in path or path.startswith('/') or path.startswith('\\'):
        logging.warning(f"检测到潜在的路径遍历: {path}")
        return None
    
    # 规范化路径
    safe_path = os.path.normpath(path)
    
    # 再次检查是否存在路径遍历
    if '..' in safe_path:
        logging.warning(f"规范化后仍存在路径遍历: {safe_path}")
        return None
    
    # 构建绝对路径
    absolute_path = os.path.abspath(os.path.join(base_dir, safe_path))
    
    # 确保路径在允许的基础目录内
    base_dir_abs = os.path.abspath(base_dir)
    if not absolute_path.startswith(base_dir_abs + os.path.sep) and absolute_path != base_dir_abs:
        logging.warning(f"路径超出允许范围: {absolute_path} 不在 {base_dir_abs} 内")
        return None
    
    return absolute_path


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
        if re.search(pattern, filename):
            logging.warning(f"文件名包含危险字符: {filename}")
            return None
    
    # 检查是否符合安全文件名规则
    if not SAFE_FILENAME_REGEX.match(filename):
        logging.warning(f"文件名不符合安全规则: {filename}")
        return None
    
    return filename


def sanitize_string(input_str: Optional[str], max_length: int = 1000) -> Optional[str]:
    """
    清理字符串，移除危险字符
    
    Args:
        input_str: 输入字符串
        max_length: 最大长度
        
    Returns:
        清理后的字符串，或 None 如果不安全
    """
    if input_str is None:
        return None
    
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # 长度检查
    if len(input_str) > max_length:
        logging.warning(f"字符串长度超出限制: {len(input_str)} > {max_length}")
        return input_str[:max_length]
    
    # 移除控制字符
    cleaned = re.sub(r'[\x00-\x1F\x7F]', '', input_str)
    
    return cleaned


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
    
    # 清理文件名
    clean_name = sanitize_filename(profile)
    if not clean_name:
        return None
    
    # 确保是 .toml 结尾
    if not clean_name.endswith('.toml'):
        clean_name += '.toml'
    
    return clean_name


def validate_params(params: dict, required: Optional[list] = None, allowed: Optional[list] = None) -> bool:
    """
    验证参数字典
    
    Args:
        params: 参数字典
        required: 必需的参数列表
        allowed: 允许的参数列表
        
    Returns:
        是否安全
    """
    if not isinstance(params, dict):
        return False
    
    # 检查必需参数
    if required:
        for key in required:
            if key not in params:
                logging.warning(f"缺少必需参数: {key}")
                return False
    
    # 检查允许的参数
    if allowed:
        for key in params:
            if key not in allowed:
                logging.warning(f"发现未授权参数: {key}")
                return False
    
    return True


def is_safe_path_component(component: str) -> bool:
    """
    检查路径组件是否安全
    """
    if not component:
        return True
    
    # 检查危险字符
    dangerous = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous:
        if char in component:
            return False
    
    return True
