#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import os
import shlex
import shutil
import subprocess
import sys


def is_admin() -> bool:
    """检查当前是否拥有管理员（Windows）或 root（Unix）权限"""
    if sys.platform == 'win32':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:
        return os.geteuid() == 0


def elevate() -> None:
    """权限不足时，通过系统原生方式提权并重新运行当前程序"""
    if is_admin():
        return

    # ── Windows ──
    if sys.platform == 'win32':
        # 构建完整的命令行参数（包含程序路径）
        args = subprocess.list2cmdline([sys.executable] + sys.argv[1:])
        # 使用 SW_HIDE (0) 避免弹出控制台窗口
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, args, None, 0
        )
        if ret <= 32:
            raise PermissionError(f"UAC 提权失败或用户取消 (错误码: {ret})")
        sys.exit(0)

    # ── macOS ──
    elif sys.platform == 'darwin':
        # 使用 AppleScript 弹出系统密码框，不依赖终端
        cmd_str = " ".join(shlex.quote(p) for p in [sys.executable] + sys.argv[1:])
        script = f'do shell script {shlex.quote(cmd_str)} with administrator privileges'

        try:
            subprocess.run(["osascript", "-e", script], check=True)
        except subprocess.CalledProcessError as e:
            raise PermissionError("用户取消授权或密码错误") from e

        # osascript 会等待子进程结束，原进程直接退出即可
        sys.exit(0)

    # ── Linux ──
    else:
        # 优先 pkexec：图形化密码框，双击运行也能用
        if shutil.which("pkexec"):
            os.execvp("pkexec", ["pkexec", sys.executable] + sys.argv[1:])

        # 回退 sudo：仅在检测到终端时可用
        elif shutil.which("sudo") and sys.stdin.isatty():
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv[1:])

        else:
            raise RuntimeError(
                "无法提权：未安装 pkexec（图形认证），"
                "或无终端环境无法使用 sudo。请在终端中运行本程序。"
            )


# ========== 使用示例 ==========
if __name__ == "__main__":
    elevate()
    print("✅ 已以高权限运行")
    # 后续放需要管理员/root 的操作...