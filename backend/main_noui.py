import logging
import os
import signal
import sys
import time
import webbrowser
import threading
from typing import Optional

from http_dispatcher import http_server
from utils import run_configs, log_util, permissions_util, ip_util, qrcode_util, et_run_info
from utils.permissions_util import ServerHandle


BASE_URI = "/cgi/ThirdParty/EasyTier-EUI/index.cgi"

def start_server(host: str, port: int, exit_on_failure: bool = False) -> Optional[ServerHandle]:
    """启动 HTTP 服务（提权 + 启动），不打开浏览器。

    返回 (success: bool, handle: ServerHandle | None)
    调用 handle.stop() 即可停止服务，无论管理员还是提权模式。
    """
    if not permissions_util.is_admin():
        try:
            handle = permissions_util.run_elevated_module(
                'http_dispatcher.http_server', args=[f'--host={host}', f'--port={port}', f'--base_uri={BASE_URI}'])
            if handle is None:
                logging.error("提权进程启动失败，返回 None")
                if exit_on_failure:
                    sys.exit(1)
                return None
            logging.info(f"提权进程已启动 PID={handle.pid}")
            return handle
        except Exception as e:
            logging.exception(f"提权启动异常: {e}")
            if exit_on_failure:
                sys.exit(1)
            return None
    else:
        logging.info(f"当前用户已是管理员权限")
        server = http_server.build(host, port, BASE_URI)
        if server is None:
            logging.error("HTTP 服务启动失败")
            if exit_on_failure:
                sys.exit(1)
            return None
        threading.Thread(target=http_server.serve_forever, args=(server,), daemon=True, name='http-server').start()
        logging.info(f"HTTP 服务已在后台线程启动")
        return ServerHandle(server=server)

def stop_server(handle: ServerHandle, port: int):
    import urllib.request
    try:
        url = f'http://127.0.0.1:{port}{BASE_URI}/api/settings/shutdown'
        logging.info(f"尝试通过 HTTP 请求关闭提权进程: {url}")
        req = urllib.request.Request(
            url,
            data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=3)
        logging.info("已通过 HTTP 请求关闭提权进程")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.warning(f"HTTP 关闭请求失败: {e}")
    finally:
        if handle._server is not None:
            try:
                handle.stop()
                logging.info("已通过 handle.stop() 停止服务")
            except Exception:
                pass


def run():
    """main_noui 完整入口：启动服务 + 打开浏览器 + 等待 Ctrl+C 停止"""
    permissions_util.handle_elevated_run()
    run_configs.setup_env()
    run_mode = run_configs.get_run_mode()
    log_util.setup_log(log_file=os.path.join(run_configs.log_dir(), 'app.log'),
                       log_level=logging.INFO if run_mode > 0 else logging.DEBUG,
                       enabled_console=run_mode == 0)
    # logging.info(f"前端路径: {os.path.join(sys._MEIPASS, 'frontend')}")

    if sys.platform != 'win32':
        # unzip 出来是 rw-r--r-- ，需要添加执行权限
        import stat
        dst = run_configs.core_dir()
        exec_path = os.path.join(dst, 'easytier-core')
        os.chmod(exec_path, os.stat(exec_path).st_mode | stat.S_IEXEC)
        exec_path = os.path.join(dst, 'easytier-cli')
        os.chmod(exec_path, os.stat(exec_path).st_mode | stat.S_IEXEC)

    global BASE_URI
    import argparse
    parser = argparse.ArgumentParser(description='CGI Proxy HTTP Server')
    parser.add_argument('--host', help='Host to bind to')
    parser.add_argument('--port', type=int, help='Port to bind to')
    parser.add_argument('--base_uri', default=BASE_URI, help=f'Base URI to use (default: {BASE_URI})')
    args = parser.parse_args()

    BASE_URI = args.base_uri
    host = args.host or run_configs.EUI_RUN_HOST or '0.0.0.0'
    port = args.port or run_configs.EUI_RUN_PORT or 5666
    handle = start_server(host, port, exit_on_failure=True)
    if handle is None:
        sys.exit(1)

    # 注册 SIGINT 处理器，确保 Ctrl+C 始终能被捕获
    _shutdown_requested = False
    def _on_sigint(signum, frame):
        nonlocal _shutdown_requested
        _shutdown_requested = True
    original_sigint = signal.signal(signal.SIGINT, _on_sigint)

    try:
        acc_host = host
        acc_port = port
        if acc_host == '0.0.0.0':
            if run_mode == 0:
                acc_host = '127.0.0.1'
            else:
                lan_ips = ip_util.get_lan_ips()
                acc_host = lan_ips[0].get('ip') if len(lan_ips) > 0 else '127.0.0.1'
        access_url = f"http://{acc_host}:{acc_port}"
        qr_code = qrcode_util.create_str(access_url)
        logging.info(f"访问地址: {access_url} , QrCode: {qr_code}")
        time.sleep(1)
        if run_mode != 0:
            webbrowser.open_new_tab(access_url)
            logging.info(f"已打开本地设备浏览器，请在浏览器上访问")
    except Exception as e:
        logging.error(f"打开本地设备不支持浏览器访问: {e}")

    try:
        logging.info("按 Ctrl+C 停止服务")
        while not _shutdown_requested:
            time.sleep(1)
    finally:
        # 恢复原始信号处理器
        signal.signal(signal.SIGINT, original_sigint)
        try:
            stop_server(handle, args.port)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    run()