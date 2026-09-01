#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
此脚本为飞牛专用，主要用于避免空跑时，让飞牛按需识别为应用开启状态。方便进入界面操作
开启应用，没有et运行，识别为运行中
关闭应用，识别为停用
重启系统，根据上次运行状态，提供方法给飞牛拉起应用，并启动原来的运行服务
"""
import logging
import os.path
import sys
from pathlib import Path

from et_adapters import get_facade
from et_adapters.core_background_adapter import CoreBackgroundAdapter

try:
    import psutil
except ImportError:
    psutil = None

from actions import services
from utils import run_configs, log_util, et_run_info, common_util

logger = logging.getLogger(__name__)
_fn_check_file :str=''

def status():
    """
    应用启动前检查一次
    应用运行期间定期轮询检查
    检查文件的开机时间是否为当前开机时间
    0 表示应用正在运行
    3 表示应用未运行
    """
    if not os.path.exists(_fn_check_file):
        logger.info(f"文件 {_fn_check_file} 不存在，应用未运行")
        return 3
    boot_time_timestamp = psutil.boot_time()
    with open(_fn_check_file, 'r') as f:
        data = f.readline()
        if data == str(boot_time_timestamp):
            return 0
        if abs(float(data) - boot_time_timestamp) < 2:
            logger.warning(f"文件 {_fn_check_file} 内容是 {data}，与当前开机时间 {boot_time_timestamp} 不一致，但误差在2秒内，应用正在运行")
            return 0
        logger.error(f"当次获取开机时间和上次记录开机时间差超过2秒，判定应用未运行")
        return 3


def start():
    """
    先调用 status(), 未执行时才调用 start()
    启动成功后，把 开机时间 写入 文件
    """
    logger.info("开始启动应用...")
    Path(run_configs.config_dir()).mkdir(parents=True, exist_ok=True)
    _fix_remove_sys_service()
    services.start_all()
    check_file = Path(_fn_check_file)
    if not check_file.exists():
        check_file.touch()
    with open(_fn_check_file, 'w') as f:
        boot_time_timestamp = str(psutil.boot_time())
        f.write(boot_time_timestamp)
        logger.info(f"文件 {_fn_check_file} 内容写入 {boot_time_timestamp} 成功，应用启动成功")

def stop():
    """
    先调用 status(), 未执行时才调用 stop()
    停止应用，不设置
    """
    services.stop_all()
    Path(_fn_check_file).unlink(missing_ok=True)
    logger.info(f"文件 {_fn_check_file} 已删除, 应用停止成功")


def _fix_remove_sys_service():
    """
    修复：移除2.0版本错误引入系统服务
    """
    if '/EasyTier-EUI/' in str(__file__):
        # 仅处理 EasyTier-EUI 版本。用户版不需要处理
        return
    logger.info("开始检查和修复系统服务...")
    ext = ".exe" if sys.platform == "win32" else ""
    cli_path = os.path.join(run_configs.core_dir(), f'easytier-cli{ext}')
    core_path = os.path.join(run_configs.core_dir(), f'easytier-core{ext}')
    service_adapter = CoreBackgroundAdapter(cli_path, core_path)
    if service_adapter.system_service_status() > -1:
        # 移除系统服务
        service_adapter.system_service_uninstall()
        logger.info(f"已移除注册的系统服务")
    infos = et_run_info.get_all()
    for info in infos.values():
        if info.use_system_service:
            logger.info(f"标记不使用系统服务: {info.profile}")
            info.use_system_service = False
            et_run_info.save(*info.__dict__.values())
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            if any('/var/apps/EasyTier-EUI/target/bin/easytier-core' in arg for arg in cmdline):
                logger.info(f"发现 EasyTier-EUI 的 et 进程: pid={proc.info['pid']}, name={proc.info['name']}, cmdline={cmdline}")
                common_util.run_cmd(f"kill -9 {proc.info['pid']}")
                logger.info(f"已移除 EasyTier-EUI 的 et 进程: pid={proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

if __name__ == '__main__':
    try:
        run_configs.setup_env()
        log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'cmd.log'), log_level=logging.WARN, enabled_console=False)
        _fn_check_file = run_configs.fn_check_file()
        args = sys.argv
        if len(args) != 2:
            print(f"传入参数错误： {args}")
            sys.exit(1)
        method = args[1]
        if method == "start":
            start()
        elif method == "stop":
            stop()
        elif method == "status":
            result = status()
            sys.exit(result)
        else:
            raise AssertionError(f"不支持的参数 {method}")
    except Exception as e:
        logger.exception(e)
        print(f"{e}", file=sys.stderr)
        sys.exit(1)