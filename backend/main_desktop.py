#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import ctypes
import logging
import os
import subprocess
import sys
import threading
import uuid
import webbrowser
from ctypes import wintypes

import main_noui
from locales import get_message, get_last_lang
from utils import run_configs, permissions_util, app_settings

logger = logging.getLogger(__name__)

ROLE_CONTROLLER = 'controller'
ROLE_WEBVIEW = 'webview'
APP_NAME = 'EasyTier-EUI'


class WindowsTrayWindow:
    """Find the WebView window from the controller, including one-file builds."""

    def __init__(self, token):
        self.property_name = f'{APP_NAME}.TrayWindow.{token}'
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.enum_callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows.argtypes = [self.enum_callback, wintypes.LPARAM]
        self.user32.SetPropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.HANDLE]
        self.user32.GetPropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
        self.user32.GetPropW.restype = wintypes.HANDLE
        self.user32.RemovePropW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
        self.user32.RemovePropW.restype = wintypes.HANDLE
        self.user32.IsIconic.argtypes = [wintypes.HWND]
        self.user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.SetForegroundWindow.argtypes = [wintypes.HWND]

    def attach(self, window):
        hwnd = window.native.Handle.ToInt64()
        if not self.user32.SetPropW(hwnd, self.property_name, 1):
            logger.warning('无法注册托盘窗口: %s', ctypes.WinError(ctypes.get_last_error()))
            return

        def hide_minimized():
            if self.user32.IsIconic(hwnd):
                self.user32.ShowWindowAsync(hwnd, 0)  # SW_HIDE

        def detach():
            self.user32.RemovePropW(hwnd, self.property_name)

        window.events.minimized += hide_minimized
        window.events.closing += detach

    def show(self):
        @self.enum_callback
        def show_matching_window(hwnd, _):
            if not self.user32.GetPropW(hwnd, self.property_name):
                return True
            if self.user32.IsIconic(hwnd):
                self.user32.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
            self.user32.SetForegroundWindow(hwnd)
            return False

        self.user32.EnumWindows(show_matching_window, 0)


def _is_frozen():
    return getattr(sys, 'frozen', False)


def _resource_dir():
    return sys._MEIPASS if _is_frozen() else os.path.dirname(os.path.abspath(__file__))


def _asset_path(name):
    return os.path.join(_resource_dir(), 'assets', name)


def _connect_host(host):
    if not host or host in ('0.0.0.0', '::', '::0', '0:0:0:0:0:0:0:0'):
        return '127.0.0.1'
    return host


def _enable_dark_mode():
    """让 Windows 托盘原生弹出菜单跟随系统暗色主题。

    pystray 的 Windows 后端用原生 Win32 菜单（CreatePopupMenu + TrackPopupMenuEx），
    默认只渲染浅色。这里调用 uxtheme.dll 未公开导出的 SetPreferredAppMode(AllowDark)，
    使本进程主动选择加入暗色模式。

    必须在创建任何窗口（即托盘窗口）之前调用，否则不生效。
    该 API 未公开（uxtheme.dll 序数 135/136），仅 Windows 10 1809+ 有效；
    macOS 由 AppKit 原生跟随系统主题，无需处理，故此处跳过。

    注意：菜单主题存在进程级缓存，程序运行期间切换系统深浅色不会即时跟随，
    需重启程序（重新创建菜单）后才会应用新主题。
    """
    if sys.platform != 'win32':
        return
    try:
        uxtheme = ctypes.windll.uxtheme
        get_proc = ctypes.windll.kernel32.GetProcAddress
        get_proc.restype = ctypes.c_void_p
        get_proc.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        # 序数 135：SetPreferredAppMode(mode)；1=AllowDark 跟随系统，2=ForceDark 强制暗色
        set_preferred = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int)(
            get_proc(uxtheme._handle, 135))
        # 序数 136：FlushMenuThemes()，刷新已缓存的菜单主题
        flush_menus = ctypes.WINFUNCTYPE(None)(
            get_proc(uxtheme._handle, 136))

        set_preferred(1)
        flush_menus()
    except Exception as e:
        logger.warning('启用 Windows 暗色菜单失败: %s', e)


def _configure_macos_regular():
    if sys.platform != 'darwin':
        return
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyRegular
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        app.activateIgnoringOtherApps_(True)
    except Exception as e:
        logger.debug('macOS 激活窗口失败: %s', e)


def _configure_macos_accessory():
    if sys.platform != 'darwin':
        return
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    except Exception as e:
        logger.debug('macOS 隐藏 Dock 图标失败: %s', e)


def run_webview_role(host, port, tray_token=None):
    main_noui.init_env()

    connect_host = _connect_host(host)
    if not port:
        port = run_configs.EUI_RUN_PORT or 5666

    import webview
    webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True

    title = f'易组网 {run_configs.build_version()}'

    class Api:
        def window_open(self, url):
            full_url = url if url.startswith('http') else f'http://{connect_host}:{port}{url}'
            logger.info('JS_API 浏览器打开地址: %s', full_url)
            webbrowser.open_new_tab(full_url)

    _configure_macos_regular()

    icon_path = _asset_path('icon.ico')
    webview_data_dir = os.path.join(run_configs.data_dir(), 'webview')
    os.makedirs(webview_data_dir, exist_ok=True)

    window = webview.create_window(
        title,
        f'http://{connect_host}:{port}',
        width=1200,
        height=750,
        text_select=True,
        js_api=Api(),
    )
    if sys.platform == 'win32' and tray_token:
        window.events.before_show += WindowsTrayWindow(tray_token).attach
    webview.start(
        private_mode=False,
        storage_path=webview_data_dir,
        icon=icon_path,
        debug=not _is_frozen(),
    )


class DesktopController:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.http_handle = None
        self.webview_proc = None
        self.icon = None
        self.tray_window_token = None
        self.tray_window = None
        self._proc_lock = threading.Lock()
        self._stopped = False
        self._stop_network_quitting = False

    def start(self):
        result = main_noui.start_server(self.host, self.port)
        self.http_handle = result['handle']
        self.host = result['host']
        self.port = result['port']
        if app_settings.get('system_tray_enabled', True):
            self._create_tray()
            self._open_window()
            try:
                self.icon.run()
            finally:
                self.stop_all()
        else:
            # 关闭系统托盘：窗口关闭即退出整个应用
            self._open_window()
            try:
                if self.webview_proc is not None:
                    self.webview_proc.wait()
            finally:
                self.stop_all()

    def _create_tray(self):
        import pystray
        from PIL import Image

        icon_path = _asset_path('icon.png' if sys.platform == 'darwin' else 'icon.ico')
        image = Image.open(icon_path)
        if sys.platform == 'darwin':
            image = image.convert('RGBA').resize((22, 22), Image.LANCZOS)

        show_label = get_message('tray.show_window', lang=get_last_lang())
        stop_network_quit_label = get_message('tray.stop_network_quit', lang=get_last_lang())
        quit_label = get_message('tray.quit', lang=get_last_lang())
        menu = pystray.Menu(
            pystray.MenuItem(show_label, self._on_show_window, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(stop_network_quit_label, self._on_stop_network_and_quit),
            pystray.MenuItem(quit_label, self._on_quit),
        )
        self.icon = pystray.Icon(APP_NAME, image, APP_NAME, menu)
        if sys.platform == 'win32':
            self.tray_window_token = uuid.uuid4().hex
            self.tray_window = WindowsTrayWindow(self.tray_window_token)
        _configure_macos_accessory()

    def _webview_cmd(self):
        args = ['--webview-role', ROLE_WEBVIEW, '--host', str(self.host), '--port', str(self.port)]
        if self.tray_window_token:
            args.extend(['--tray-window-token', self.tray_window_token])
        if _is_frozen():
            return [sys.executable] + args
        return [sys.executable, os.path.abspath(__file__)] + args

    def _open_window(self):
        with self._proc_lock:
            if self.webview_proc is not None and self.webview_proc.poll() is None:
                if self.tray_window is not None:
                    self.tray_window.show()
                return
            cmd = self._webview_cmd()
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            try:
                self.webview_proc = subprocess.Popen(cmd, creationflags=creationflags)
                logger.info('已启动 webview 子进程 PID=%s', self.webview_proc.pid)
            except Exception as e:
                logger.exception('启动 webview 子进程失败: %s', e)

    def _stop_webview(self):
        with self._proc_lock:
            proc = self.webview_proc
            self.webview_proc = None
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _on_show_window(self, icon, item):
        self._open_window()

    def _on_stop_network_and_quit(self, icon, item):
        if self._stop_network_quitting:
            return
        self._stop_network_quitting = True
        try:
            from actions import services
            services.stop_all()
        except Exception:
            logger.exception('停组网并退出UI：停止组网失败')
        finally:
            self._on_quit(icon, item)

    def _on_quit(self, icon, item):
        self.stop_all()
        icon.stop()

    def stop_all(self):
        if self._stopped:
            return
        self._stopped = True
        self._stop_webview()
        if self.http_handle is not None:
            main_noui.stop_server(self.http_handle, self.port)


def main():
    permissions_util.handle_elevated_run()

    parser = argparse.ArgumentParser(description='EasyTier-EUI 桌面控制器')
    # --webview-role: 指定当前进程的角色（同一脚本两种运行模式）
    #   controller（默认）: 控制器进程，常驻托盘 + 启动 HTTP 服务
    #   webview          : 窗口进程，由控制器以子进程方式拉起，仅负责显示 webview，关闭即退出释放内存
    parser.add_argument('--webview-role', choices=[ROLE_CONTROLLER, ROLE_WEBVIEW], default=ROLE_CONTROLLER)
    # --host: HTTP 服务监听地址；不传时由 start_server 自动决定
    parser.add_argument('--host', default=None)
    # --port: HTTP 服务监听端口；不传时自动分配或使用默认端口（run_configs.EUI_RUN_PORT / 5666）
    parser.add_argument('--port', type=int, default=None)
    parser.add_argument('--tray-window-token', help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.webview_role == ROLE_WEBVIEW:
        run_webview_role(args.host, args.port, args.tray_window_token)
        return

    _enable_dark_mode()
    controller = DesktopController(args.host, args.port)
    try:
        controller.start()
    except BaseException:
        logger.exception('程序异常退出')
        raise
    finally:
        controller.stop_all()


if __name__ == '__main__':
    main()
