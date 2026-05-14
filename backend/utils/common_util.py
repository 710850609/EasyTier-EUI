#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import shutil
import subprocess
import sys


def run_cmd(command, *args, shell=False) -> str:
    """
    执行命令并返回 JSON 格式结果
    
    Args:
        command: 命令（字符串或列表）
        *args: 命令参数（当 command 为字符串时）
        shell: 是否使用 shell 执行
    
    Returns:
        JSON 字符串: {"code": 状态码, "stdout": 标准输出, "stderr": 错误输出, "success": 是否成功}
    """
    # logging.debug(f"执行命令: {command} {' '.join(args)}")
    # 构建命令列表
    if shell:
        # shell 模式：合并为字符串
        if args:
            full_command = f"{command} {' '.join(args)}"
        else:
            full_command = command
        cmd = full_command
    else:
        # 非 shell 模式：使用列表
        if args:
            cmd = [command] + list(args)
        else:
            cmd = command if isinstance(command, list) else command.split()
    
    # 设置 Windows 下不弹出控制台窗口
    creationflags = 0
    if sys.platform == 'win32' and not shell:
        creationflags = subprocess.CREATE_NO_WINDOW
    
    # 执行命令
    result = subprocess.run(
        cmd,
        shell=shell,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',  # 遇到无法解码的字符用 � 替换
        timeout=3600,  # 1小时超时
        creationflags=creationflags
    )
    if result.returncode == 0:
        return result.stdout.strip() if result.stdout else ""
    error_msg = result.stderr.strip() if result.stderr else ""
    raise Exception(f"{error_msg}")


def move(src_path, dst_path):
    """
    移动文件或目录（纯Python实现，支持多平台）
    
    Args:
        src_path: 源路径
        dst_path: 目标路径
    """
    
    # 确保源路径存在
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"源路径不存在: {src_path}")
    
    # 如果目标已存在，先删除
    if os.path.exists(dst_path):
        if os.path.isdir(dst_path):
            shutil.rmtree(dst_path)
        else:
            os.remove(dst_path)
    
    # 移动文件或目录
    shutil.move(src_path, dst_path)

def delete(path):
    """删除目录，如果是软链接则先解析真实路径再删除"""
    if os.path.islink(path):
        # 获取软链接指向的真实路径
        real_path = os.path.realpath(path)
        print(f"软链接 {path} 指向 {real_path}")
        # 先删除软链接本身
        os.unlink(path)
        # 再删除真实目录（如果存在）
        if os.path.exists(real_path):
            shutil.rmtree(real_path)
    elif os.path.exists(path):
        logging.debug(f"删除路径: {path}")
        shutil.rmtree(path)