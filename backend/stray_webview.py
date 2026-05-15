import os
import threading
import webview
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item


class TrayIcon:
    """系统托盘图标，依赖外部传入 window 对象进行操作"""

    def __init__(self, win_title: str, window=None):
        self.win_title = win_title
        self.window = window              # webview Window 对象，由 StrayWin 注入
        self.is_window_visible = True
        self.is_exiting = False
        self.tray_icon = None

    def _create_default_icon(self):
        image = Image.new('RGB', (64, 64), color='#1E88E5')
        draw = ImageDraw.Draw(image)
        draw.rectangle([(16, 16), (48, 48)], fill='white')
        return image

    def _load_icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')
        try:
            return Image.open(icon_path)
        except (FileNotFoundError, IOError):
            return self._create_default_icon()

    def _on_show_hide(self, icon, item):
        """单击托盘图标：显示/隐藏窗口"""
        if not self.window:
            return
        if self.is_window_visible:
            self.window.hide()
            self.is_window_visible = False
        else:
            self.window.show()
            self.is_window_visible = True

    def _on_quit(self, icon, item):
        """退出应用"""
        self.is_exiting = True
        if self.window:
            self.window.destroy()

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


class StrayWin:
    """主窗口 + 托盘组合控制器"""

    def __init__(self, url: str, win_title: str, win_width: int = 1100, win_height: int = 680):
        self.url = url
        self.win_title = win_title
        self.win_width = win_width
        self.win_height = win_height
        self.window = None
        self.tray = None                    # TrayIcon 实例

    def show(self):
        """主线程运行 webview，托盘在后台线程"""
        # 1. 先创建 webview 窗口
        self.window = webview.create_window(
            self.win_title, self.url,
            width=self.win_width, height=self.win_height
        )

        # 2. 创建托盘，注入 window 引用
        self.tray = TrayIcon(self.win_title, window=self.window)
        self.tray.build()

        # 3. 托盘在后台线程运行（run() 是阻塞的，必须包线程）
        threading.Thread(target=self.tray.run, daemon=True).start()

        # 4. 主线程启动 webview（Windows 必须主线程）
        webview.start()

    def minimize_to_tray(self):
        if self.tray:
            self.tray._on_show_hide(None, None)   # 复用托盘回调

    def restore_from_tray(self):
        if self.tray and not self.tray.is_window_visible:
            self.window.show()
            self.tray.is_window_visible = True

    def exit(self):
        """安全退出"""
        if self.tray:
            self.tray.stop()
        if self.window:
            self.window.destroy()


if __name__ == '__main__':
    win = StrayWin(
        'http://192.168.220.12:5666/cgi/ThirdParty/EasyTier-Lite/index.cgi',
        '易组网'
    )
    win.show()