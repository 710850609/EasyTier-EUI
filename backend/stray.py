import logging
import os
import platform
import signal
import sys
import threading

from PIL import Image, ImageDraw

import http_server
import stray_win

host='127.0.0.1'
port=5666
base_url = '/cgi/ThirdParty/EasyTier-Lite/index.cgi'
window_title = "易组网 | EasyTier"  # 请确保前端 HTML 的 <title> 设置为这个值

# 全局停止标志
_stop_event = threading.Event()
_use_chinese = True
# 全局图标引用，用于信号处理
_global_icon = None
_global_server = None
_stray_win = stray_win.StrayWin(f'http://{host}:{port}{base_url}', window_title)


def start_web():
    def web_server():
        global _global_server
        _global_server = http_server.build_server(host, port, base_url)
        try:
            _global_server.serve_forever()
        except KeyboardInterrupt:
            logging.info("Server stopped by user")
            _global_server.shutdown()

    server_thread = threading.Thread(target=web_server, daemon=True)
    server_thread.start()
    return server_thread

def stop_web():
    if _global_server:
        logging.info(f"停止Web服务...")
        _global_server.shutdown()


def on_quit(icon, item):
    """点击菜单时，退出程序"""
    logging.info(f"退出系统托盘...")
    stop()
    _stop_event.set()  # 通知主线程退出

def stop_stray_icon():
    logging.info(f"停止系统托盘...")
    if _global_icon:
        _global_icon.stop()


def start_tray_icon():
    global _global_icon
    global _use_chinese

    # 设置 pystray 后端为 gtk 以支持中文（X11 后端使用 latin-1 编码，不支持中文）
    # 可选后端: appindicator, gtk, xorg, darwin, win32
    # os.environ['PYSTRAY_BACKEND'] = 'gtk'
    try:
        import pystray
    except Exception as e:
        logging.exception("当前系统不支持系统托盘功能")
        if "Namespace AyatanaAppIndicator3 not available" in str(e):
            # 强制使用 GTK 后端（避免 AppIndicator 缺失问题）
            # 必须在 import pystray 之前设置
            if platform.system() == "Linux":
                os.environ['PYSTRAY_BACKEND'] = 'gtk'
                print(f"{e}。强制Linux使用 GTK 环境")
                import pystray
                _use_chinese = False
        else:
            print(f"pystray 模块加载失败，无法使用托盘图标功能: {e}")
            raise ImportError("pystray 模块加载失败") from e

    def create_image():
        """加载应用图标"""
        # 获取图标路径（支持开发和打包后的环境）
        res_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        icon_path = os.path.join(os.path.abspath(res_dir), 'assets', 'icon.png')

        if os.path.exists(icon_path):
            return Image.open(icon_path)
        else:
            # 如果找不到图标，生成默认图标
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), 'dodgerblue')
            draw = ImageDraw.Draw(image)
            draw.rectangle((width / 4, height / 4, width * 3 / 4, height * 3 / 4), fill='white')
            return image
    try:

        if _use_chinese:
            menu = pystray.Menu(
                pystray.MenuItem('显示窗口', _stray_win.show, default=True),
                pystray.MenuItem('最小化窗口', _stray_win.minimize),
                pystray.MenuItem('退出', on_quit)
            )
            icon = pystray.Icon("易组网", create_image(), "易组网", menu)
        else:
            menu = pystray.Menu(
                pystray.MenuItem('Show Window', _stray_win.show, default=True),
                pystray.MenuItem('Minimize Window', _stray_win.minimize),
                pystray.MenuItem('Quit', on_quit)
            )
            icon = pystray.Icon("EasyTier-Lite", create_image(), "EasyTier-Lite", menu)
        
        _global_icon = icon
        icon.run()
    except Exception as e:
        print(f"Tray icon error: {e}")
        print("Note: System tray requires a desktop environment")


def start_tray():
    """启动托盘图标（如果支持）"""
    try:
        tray_thread = threading.Thread(target=start_tray_icon, daemon=True)
        tray_thread.start()
        return tray_thread
    except Exception as e:
        print(f"Failed to start tray: {e}")
        return None

def setup_windows_console_handler():
    """Windows 控制台关闭事件处理"""
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        
        # Windows 控制台控制信号
        CTRL_C_EVENT = 0
        CTRL_BREAK_EVENT = 1
        CTRL_CLOSE_EVENT = 2
        
        handler_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
        
        def handler(ctrl_type):
            if ctrl_type in (CTRL_C_EVENT, CTRL_BREAK_EVENT, CTRL_CLOSE_EVENT):
                logging.info("收到退出信号，正在关闭...")
                stop()
                _stop_event.set()
                return True
            return False
        
        # 设置控制台控制处理程序
        kernel32 = ctypes.windll.kernel32
        SetConsoleCtrlHandler = kernel32.SetConsoleCtrlHandler
        SetConsoleCtrlHandler.argtypes = [handler_type, wintypes.BOOL]
        SetConsoleCtrlHandler.restype = wintypes.BOOL
        
        # 创建处理函数实例并保持引用
        _handler_instance = handler_type(handler)
        SetConsoleCtrlHandler(_handler_instance, True)
        return _handler_instance
    return None

def setup():
    # --- 3. 主程序启动托盘线程 ---
    # 注册 Ctrl+C 信号处理（必须在主线程）
    def signal_handler(sig, frame):
        stop()
        _stop_event.set()

    if sys.platform == 'win32':
        # Windows 使用控制台事件处理
        _win_handler = setup_windows_console_handler()
    else:
        # Linux/macOS 使用信号
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    tray_thread = start_tray()
    start_web()
    _stray_win.show()
    if tray_thread:
        # 使用事件等待，支持中断
        try:
            while not _stop_event.is_set():
                _stop_event.wait(1)
        except KeyboardInterrupt:
            print("\n收到 KeyboardInterrupt，正在关闭...")
    else:
        print("Running without system tray...")
        # 保持程序运行
        while not _stop_event.is_set():
            try:
                _stop_event.wait(1)
            except KeyboardInterrupt:
                break

def stop():
    logging.info("正在关闭资源...")
    _stray_win.exit()
    stop_web()
    stop_stray_icon()

if __name__ == '__main__':
    setup()