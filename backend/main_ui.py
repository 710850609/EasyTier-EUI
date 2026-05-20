import logging
import os
import sys
import threading

import webview

import http_server
from utils import run_configs, log_util


class WebWin:
    """主窗口 + 托盘组合控制器"""

    def __init__(self, win_title: str, win_width: int = 1100, win_height: int = 680):
        self.win_title = win_title
        self.win_width = win_width
        self.win_height = win_height
        self.is_window_visible = False
        host = '127.0.0.1'
        port = 5666
        """主线程运行 webview，托盘在后台线程"""
        self.web_server = WebServer(host=host, port=port)
        threading.Thread(target=self.web_server.run, daemon=True).start()

        webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True
        self.window = webview.create_window(
            self.win_title, f'http://{host}:{port}',
            width=self.win_width, height=self.win_height,
            text_select=True
        )
        res_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        icon_path = os.path.join(os.path.abspath(res_dir), 'assets', 'icon.ico')
        webview_data_dir = os.path.join(run_configs.data_dir(), 'webview')
        os.makedirs(webview_data_dir, exist_ok=True)
        # linux 上指定qt后端
        webview.start(
            private_mode=False, # # 关闭隐私模式，开启数据持久化
            storage_path=webview_data_dir,
            icon=icon_path,
            debug=not getattr(sys, 'frozen', False),
        )
        self.is_window_visible = True

    def toggle_show(self):
        if self.is_window_visible:
            self.window.hide()
            self.is_window_visible = False
        else:
            self.window.show()
            self.is_window_visible = True

    def destroy(self):
        if self.web_server:
            self.web_server.stop()
        if self.window:
            self.window.destroy()

    def exit(self):
        """安全退出"""
        self.destroy()

class WebServer:
    def __init__(self, host='127.0.0.1', port=5666, base_url=None):
        self.host = host
        self.port = port
        self.base_url = base_url
        self.server = None

    def run(self):
        """在后台线程启动 HTTP 服务器"""
        try:
            self.server = http_server.build_server(self.host, self.port, self.base_url)
            logging.info(f"HTTP 服务启动: http://{self.host}:{self.port}")
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


if __name__ == '__main__':
    run_configs.setup_env()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'), log_level=logging.INFO,
                       enabled_console=True)
    win = WebWin('易组网')
