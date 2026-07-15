import logging
import os
import sys
import webbrowser

import webview

import main_noui
from utils import run_configs, log_util


class WebWin:
    """主窗口 + 托盘组合控制器"""

    def __init__(self, host: str, port: int, win_title: str, win_width: int = 1200, win_height: int = 750):
        self.win_title = win_title
        self.win_width = win_width
        self.win_height = win_height
        self.host = host
        self.port = port
        self.is_window_visible = False
        self.http_server = main_noui.start_server(host, port)
        if self.http_server is None:
            logging.error("已运行实例")
            sys.exit(1)

        webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True

        class Api:
            def window_open(self, url):
                full_url = url if url.startswith('http') else f'http://{host}:{port}{url}'
                logging.info(f"JS_API 浏览器打开地址: {full_url}")
                webbrowser.open_new_tab(full_url)

        self.window = webview.create_window(
            self.win_title, f'http://{host}:{port}',
            width=self.win_width, height=self.win_height,
            text_select=True,
            js_api=Api()
        )
        res_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        icon_path = os.path.join(os.path.abspath(res_dir), 'assets', 'icon.ico')
        webview_data_dir = os.path.join(run_configs.data_dir(), 'webview')
        os.makedirs(webview_data_dir, exist_ok=True)
        webview.start(
            private_mode=False,
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

    def exit(self):
        if self.http_server:
            main_noui.stop_server(self.http_server, self.port)
        if self.window:
            self.window.destroy()
            logging.info("关闭窗口")

if __name__ == '__main__':
    run_configs.setup_env()
    run_mode = run_configs.get_run_mode()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'),
                       log_level=logging.INFO if run_mode > 0 else logging.DEBUG,
                       enabled_console=run_mode == 0)
    import argparse
    parser = argparse.ArgumentParser(description='CGI Proxy HTTP Server')
    parser.add_argument('--host', help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to bind to')
    args = parser.parse_args()
    ver = run_configs.build_version()
    win = None
    try:
        host = args.host or run_configs.EUI_RUN_HOST or '127.0.0.1'
        port = args.port or run_configs.EUI_RUN_PORT or 5666
        win = WebWin(host, port, f'易组网 {ver}')
    except BaseException:
        logging.exception("程序异常退出")
        raise
    finally:
        if win:
            win.exit()