import logging
import platform
import shutil
import subprocess
import time
import tkinter as tk
import webbrowser

import pygetwindow as gw


class StrayWin:

    def __init__(self, url: str, win_title:str, win_width:int = 1100, win_height:int = 680):
        self.url = url
        self.win_title = win_title
        self.win_width = win_width
        self.win_height = win_height
        pass

    def show(self):
        """将浏览器窗口显示到前端"""
        win = self.__find_window()
        if win:
            try:
                if win.isMinimized:  # 如果最小化了，先还原
                    win.restore()
                win.activate()  # 激活窗口（带到前端）
            except Exception as e:
                logging.error(f"显示窗口失败: {e}")
        else:
            logging.debug("未找到浏览器窗口，打开主页")
            self.open_url_in_app_mode()

    def minimize(self):
        """最小化浏览器窗口"""
        win = self.__find_window()
        if win:
            try:
                win.minimize()
            except Exception as e:
                logging.error(f"最小化窗口失败: {e}")
        else:
            logging.warning("未找到浏览器窗口，请先打开主页")

    def exit(self):
        """点击菜单时，退出程序"""
        win = self.__find_window()
        if win:
            try:
                win.close()
            except Exception as e:
                logging.error(f"关闭窗口失败: {e}")
        else:
            logging.warning("未找到浏览器窗口")


    def __find_window(self):
        """根据标题查找对应的浏览器窗口，返回第一个匹配的 Window 对象，否则 None"""
        try:
            windows = gw.getWindowsWithTitle(self.win_title)
            # 如果标题不完全匹配，也可以用模糊匹配
            # windows = [w for w in gw.getAllWindows() if WINDOW_TITLE in w.title]
            if windows:
                return windows[0]  # 取第一个匹配的
        except Exception as e:
            logging.error(f"查找窗口失败: {e}")
        return None


    def __get_screen_size(self):
        """获取主显示器分辨率 (width, height)"""
        try:
            root = tk.Tk()
            root.withdraw()
            w = root.winfo_screenwidth()
            h = root.winfo_screenheight()
            root.destroy()
            return w, h
        except Exception:
            # tkinter 不可用时回退到常见尺寸
            return 1920, 1080

    def __get_browser_path_from_registry(self, browser_key):
        """从注册表获取浏览器路径"""
        try:
            import winreg
            # HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths') as key:
                with winreg.OpenKey(key, f'{browser_key}.exe') as subkey:
                    return winreg.QueryValue(subkey, None)
        except FileNotFoundError:
            return None

    def __resize_window(self, pos_x, pos_y, win_width, win_height):
        """通过窗口标题查找并调整窗口大小（依赖 pygetwindow），每500ms重试一次，最多3秒"""
        if platform.system() != 'Windows':
            return False

        deadline = time.time() + 3.0
        while time.time() < deadline:
            windows = gw.getWindowsWithTitle(self.win_title)
            if windows:
                win = windows[0]
                try:
                    win.moveTo(pos_x, pos_y)
                    win.resizeTo(win_width, win_height)
                    return True
                except Exception:
                    pass  # 如果调整失败，继续重试
            time.sleep(0.3)
        return False

    def open_url_in_app_mode(self, width=1100, height=680):
        """
        在应用模式下打开 URL，窗口居中。
        返回 True 表示成功以应用模式打开，False 表示回退到普通浏览器窗口。
        """
        url = self.url
        system = platform.system()
        screen_w, screen_h = self.__get_screen_size()
        # 计算窗口左上角坐标使其居中
        pos_x = max(0, (screen_w - width) // 2)
        pos_y = max(0, (screen_h - height) // 2)

        # 通用参数：应用模式、大小、位置（Chromium 系均支持）
        chrom_args = [
            f'--window-size={width},{height}',
            f'--window-position={pos_x},{pos_y}',
            '--new-window',
            f'--app={url}',
        ]

        if system == 'Windows':
            # Windows 平台常见浏览器（按优先级）
            browsers = {
                'msedge': 'Microsoft Edge',
                'chrome': 'Google Chrome',
                'chromium': 'Chromium',
                'brave': 'Brave Browser',
                'vivaldi': 'Vivaldi',
                'opera': 'Opera',
            }
            for reg_key, _ in browsers.items():
                path = self.__get_browser_path_from_registry(reg_key)
                if path:
                    try:
                        subprocess.Popen([path] + chrom_args)
                        self.__resize_window(pos_x, pos_y, self.win_width, self.win_height)
                        return True
                    except Exception as e:
                        logging.exception(f'忽略打开 {reg_key} 浏览器失败，继续重试其他')
                        continue

            # Firefox 不支持 --app，改用 --new-window 并设置大小（位置需用脚本）
            ff_path = self.__get_browser_path_from_registry('firefox')
            if ff_path:
                try:
                    subprocess.Popen([ff_path, '--new-window', url, f'--width={width}', f'--height={height}'])
                    self.__resize_window(pos_x, pos_y, self.win_width, self.win_height)
                    return True
                except Exception as e:
                    logging.exception(f'打开 {ff_path} 浏览器失败')
                    pass

        elif system == 'Darwin':  # macOS
            # Safari 不支持命令行参数，用 AppleScript 打开并设置 bounds
            try:
                script = f'''
                tell application "Safari"
                    activate
                    open location "{url}"
                    delay 1
                    set bounds of front window to {{{pos_x}, {pos_y}, {pos_x + width}, {pos_y + height}}}
                end tell
                '''
                subprocess.run(['osascript', '-e', script])
                return True
            except Exception as e:
                logging.exception(f'打开 Safari 浏览器失败')
                pass

            # 常用 Mac 浏览器及其路径关键字
            mac_browsers = [
                ('com.microsoft.edgemac', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
                ('com.google.Chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                ('org.chromium.Chromium', '/Applications/Chromium.app/Contents/MacOS/Chromium'),
                ('com.brave.Browser', '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'),
            ]
            for bundle_id, default_path in mac_browsers:
                # 优先用 bundle id 定位，避免用户安装路径变化
                cmd = ['mdfind', f'kMDItemCFBundleIdentifier == "{bundle_id}"']
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    paths = [p for p in res.stdout.strip().split('\n') if p.endswith('.app')]
                    if paths:
                        app_path = paths[0] + '/Contents/MacOS/' + bundle_id.split('.')[-1]
                    else:
                        app_path = default_path
                except Exception as e:
                    logging.error(f'打开 {default_path} 浏览器失败, 使用默认 {default_path}')
                    app_path = default_path

                if shutil.which(app_path) or app_path.startswith('/'):
                    try:
                        # macOS 下 Chromium 也支持 --app 和位置参数
                        subprocess.Popen([app_path, '--args'] + chrom_args)
                        return True
                    except Exception as e:
                        logging.exception(f'打开 {app_path} 浏览器失败')
                        continue

            # Firefox on Mac
            ff_path = shutil.which('firefox') or '/Applications/Firefox.app/Contents/MacOS/firefox'
            if ff_path:
                try:
                    subprocess.Popen([ff_path, '--new-window', url, '--width', str(width), '--height', str(height)])
                    time.sleep(2)
                    script = f'''
                    tell application "Firefox"
                        activate
                        set bounds of front window to {{{pos_x}, {pos_y}, {pos_x + width}, {pos_y + height}}}
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', script])
                    return True
                except Exception:
                    logging.exception(f'打开 firefox 浏览器失败')
                    pass

        elif system == 'Linux':
            # 常见 Linux 浏览器
            browsers = ['microsoft-edge', 'google-chrome', 'chromium', 'brave-browser', 'vivaldi', 'opera']
            for browser in browsers:
                path = shutil.which(browser)
                if path:
                    try:
                        subprocess.Popen([path] + chrom_args)
                        return True
                    except Exception:
                        logging.exception(f'打开 firefox 浏览器失败')
                        continue

            # Firefox on Linux
            ff_path = shutil.which('firefox')
            if ff_path:
                try:
                    subprocess.Popen([ff_path, '--new-window', url, '--width', str(width), '--height', str(height)])
                    # 使用 xdotool 移动窗口（需要安装 xdotool）
                    time.sleep(2)
                    subprocess.run(['xdotool', 'search', '--name', self.win_title,
                                    'windowmove', str(pos_x), str(pos_y)], capture_output=True)
                    subprocess.run(['xdotool', 'search', '--name', self.win_title,
                                    'windowsize', str(width), str(height)], capture_output=True)
                    return True
                except Exception:
                    logging.exception(f'打开 firefox 浏览器失败')
                    pass

        # 全部失败，回退到普通打开方式
        logging.info("无法以应用模式打开，回退到普通浏览器窗口")
        webbrowser.open_new(url)
        return False


if __name__ == '__main__':
    win = StrayWin('http://127.0.0.1:5666/cgi/ThirdParty/EasyTier-Lite/index.cgi', '易组网 | EasyTier')
    win.show()
    time.sleep(10)
    win.exit()