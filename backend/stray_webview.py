import logging
import os
import sys
import threading
import webview
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item

import http_server


class WebWin:
    """主窗口 + 托盘组合控制器"""

    def __init__(self, url: str, win_title: str, win_width: int = 1100, win_height: int = 680):
        self.url = url
        self.win_title = win_title
        self.win_width = win_width
        self.win_height = win_height
        self.tray = None
        self.is_window_visible = False
        self.web_server = WebServer()
        self.web_server.start()
        """主线程运行 webview，托盘在后台线程"""
        # 1. 先创建 webview 窗口
        self.window = webview.create_window(
            self.win_title, self.url,
            width=self.win_width, height=self.win_height
        )
        if sys.platform == 'win32':
            # 2. 创建托盘，注入 window 引用
            self.tray = TrayIcon(self.win_title, window=self)
            self.tray.build()
            # 3. 托盘在后台线程运行（run() 是阻塞的，必须包线程）
            threading.Thread(target=self.tray.run, daemon=True).start()
        # 4. 主线程启动 webview（Windows 必须主线程）
        webview.start()

    def toggle_show(self):
        if self.is_window_visible:
            self.window.hide()
            self.is_window_visible = False
        else:
            self.window.show()
            self.is_window_visible = True

    def restore_from_tray(self):
        if self.tray and not self.tray.is_window_visible:
            self.window.show()
            self.tray.is_window_visible = True

    def destroy(self):
        if self.web_server:
            self.web_server.stop()
        if self.window:
            self.window.destroy()

    def exit(self):
        """安全退出"""
        if self.tray:
            self.tray.stop()
        self.destroy()

class WebServer:
    def __init__(self, host='127.0.0.1', port=5666, base_url=None):
        self.host = host
        self.port = port
        self.base_url = base_url
        self.server = None
        self._thread = None

    def start(self):
        """在后台线程启动 HTTP 服务器"""
        self.server = http_server.build_server(self.host, self.port, self.base_url)
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        logging.info(f"HTTP 服务已启动: http://{self.host}:{self.port}")

    def _serve(self):
        try:
            self.server.serve_forever()
        except Exception as e:
            logging.error(f"服务器错误: {e}")
        finally:
            if self.server:
                self.server.server_close()

    def stop(self):
        if self.server:
            logging.info("停止 Web 服务...")
            self.server.shutdown()
            self.server.server_close()


class TrayIcon:
    """系统托盘图标，依赖外部传入 window 对象进行操作"""

    def __init__(self, win_title: str, window: WebWin=None):
        self.win_title = win_title
        self.window = window
        self.is_window_visible = True
        self.is_exiting = False
        self.tray_icon = None

    def _create_default_icon(self):
        image = Image.new('RGB', (64, 64), color='#1E88E5')
        draw = ImageDraw.Draw(image)
        draw.rectangle([(16, 16), (48, 48)], fill='white')
        return image

    def _load_icon(self):
        res_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        icon_path = os.path.join(os.path.abspath(res_dir), 'assets', 'icon.png')
        try:
            return Image.open(icon_path)
        except (FileNotFoundError, IOError):
            return self._create_default_icon()

    def _on_show_hide(self, icon, item):
        """单击托盘图标：显示/隐藏窗口"""
        if self.window:
            self.window.toggle_show()

    def _on_quit(self, icon, item):
        """退出应用"""
        self.stop()

    def build(self):
        """构建并返回 pystray.Icon 实例（不启动）"""
        image = self._load_icon()
        menu = pystray.Menu(
            item("显示/隐藏窗口", self._on_show_hide, default=True),
            item("退出", self._on_quit)
        )
        self.tray_icon = pystray.Icon(
            name=self.win_title,
            icon=image,
            title=self.win_title,
            menu=menu
        )
        return self.tray_icon

    def run(self):
        """后台线程中启动托盘（阻塞方法，需包 threading）"""
        if not self.tray_icon:
            self.build()
        self.tray_icon.run()

    def run_detached(self):
        """非阻塞启动（如果 pystray 版本支持）"""
        if not self.tray_icon:
            self.build()
        self.tray_icon.run_detached()

    def stop(self):
        if self.tray_icon:
            self.tray_icon.stop()
        if self.window:
            self.window.destroy()



if __name__ == '__main__':
    win = WebWin(
        'http://127.0.0.1:5666/cgi/ThirdParty/EasyTier-Lite/index.cgi',
        '易组网'
    )