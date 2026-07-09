# -*- coding: utf-8 -*-
"""
国际化支持 - 后端语言包
"""
import re
from contextvars import ContextVar
from typing import Dict, Any

from . import zh_CN
from . import en_US

# 支持的语言
SUPPORTED_LANGS = {
    'zh_CN': zh_CN.MESSAGES,
    'en_US': en_US.MESSAGES,
}

# 默认语言
DEFAULT_LANG = 'zh_CN'

# 上下文变量：存储当前请求的语言，线程/协程安全
lang_ctx: ContextVar[str] = ContextVar('current_lang', default=DEFAULT_LANG)


def parse_accept_language(accept_lang: str) -> str:
    """
    解析 Accept-Language header，返回最匹配的支持语言
    
    Args:
        accept_lang: Accept-Language header 值
        
    Returns:
        'zh_CN' 或 'en_US'
    """
    if not accept_lang:
        return DEFAULT_LANG
    
    # 分割语言标签，按权重排序
    languages = []
    for part in accept_lang.split(','):
        part = part.strip()
        if not part:
            continue
        if ';' in part:
            lang, q = part.split(';', 1)
            lang = lang.strip()
            if 'q=' in q:
                try:
                    q = float(q.split('q=')[1])
                except (ValueError, IndexError):
                    q = 1.0
            else:
                q = 1.0
        else:
            lang = part
            q = 1.0
        languages.append((-q, lang))
    
    # 按权重降序排序
    languages.sort()
    
    # 匹配支持的语言
    for _, lang in languages:
        lang = lang.lower()
        if lang.startswith('zh'):
            return 'zh_CN'
        if lang.startswith('en'):
            return 'en_US'
    
    return DEFAULT_LANG


def set_lang(lang: str) -> None:
    """
    设置当前请求的语言
    
    Args:
        lang: 语言代码 'zh_CN' 或 'en_US'
    """
    lang_ctx.set(lang)


def get_lang() -> str:
    """
    获取当前请求的语言
    
    Returns:
        语言代码
    """
    return lang_ctx.get()


def get_message(key: str, **kwargs: Any) -> str:
    """
    获取翻译消息
    
    Args:
        key: 消息键，格式如 "error.module_load_failed"
        **kwargs: 插值参数
        
    Returns:
        翻译后的字符串，如果key不存在返回key本身
    """
    lang = lang_ctx.get()
    lang_messages = SUPPORTED_LANGS.get(lang, SUPPORTED_LANGS[DEFAULT_LANG])
    
    # 逐级查找
    current = lang_messages
    for part in key.split('.'):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            # key不存在，返回原key
            return key
    
    if not isinstance(current, str):
        return key
    
    # 处理插值 {name} {count} 等
    def replace_param(match):
        param_name = match.group(1)
        if param_name in kwargs:
            return str(kwargs[param_name])
        return match.group(0)
    
    return re.sub(r'\{(\w+)\}', replace_param, current)