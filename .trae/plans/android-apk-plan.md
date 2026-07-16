# EasyTier-EUI Android APK 任务分解与实施计划

## 方案概述

**方案**：Rust FFI + WebView 复用前端 + 内置 Python 复用后端

**核心思路**：
- 将 EasyTier Rust 源码编译为 FFI 共享库 (`libeasytier.so`)
- 使用 Chaquopy 在 Android 中嵌入 Python 运行时，复用现有 Python Backend 代码
- 使用 WebView 加载现有 Vue 3 前端，零改动复用
- 通过 Android VpnService 实现 VPN 功能，Rust FFI 适配 TUN→VpnService fd

**总预估工时**：~30 人天 | **建议团队**：1-2 人

---

## 一、里程碑

```
M0: 环境搭建验证 ──→ M1: Rust FFI 编译 ──→ M2: Backend 适配 ──→ M3: 联调测试 ──→ M4: 发布
     (3天)              (7天)                (7天)               (5天)            (3天)
```

---

## 二、架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        Android APK                                │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   WebView 容器                               │ │
│  │         加载现有 Vue 3 前端（100% 复用）                       │ │
│  │         HTTP → http://127.0.0.1:{port}/api/...               │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │ HTTP (localhost)                    │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │              Embedded Python (Chaquopy)                       │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │  现有 Backend 代码（90%+ 复用）                          │  │ │
│  │  │  • http_dispatcher/dispatcher.py（路由分发）              │  │ │
│  │  │  • actions/services.py（服务管理）                       │  │ │
│  │  │  • actions/peers.py（节点管理）                          │  │ │
│  │  │  • actions/configs.py（配置管理）                        │  │ │
│  │  │  • actions/settings.py（设置管理）                       │  │ │
│  │  │  • actions/monitor.py（监控）                            │  │ │
│  │  │  • actions/et_core.py（核心管理）                        │  │ │
│  │  │  • utils/*（工具函数）                                    │  │ │
│  │  │  • locales/*（国际化）                                   │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  │                          │                                    │ │
│  │              修改点：subprocess → Rust FFI 调用               │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │ Chaquopy JNI / PyJNIus              │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │                  Kotlin/Java 桥接层                           │ │
│  │  • VpnService 实现（Android VPN 系统服务）                     │ │
│  │  • JNI → Rust FFI 封装                                       │ │
│  │  • 启动/管理 Embedded Python 进程                             │ │
│  │  • 本地 HTTP Server 启动（替代 CGI 模式）                      │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │ JNI                                 │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │          Rust FFI 共享库 (libeasytier.so)                    │ │
│  │  • EasyTier 核心逻辑（P2P 组网 / 加密 / 中继）                │ │
│  │  • TUN 设备 → VpnService FileDescriptor 适配                  │ │
│  │  • 暴露 C ABI 接口                                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## 三、Phase 0：环境搭建与可行性验证（3 天）

### Task 0.1：Android 项目初始化（0.5 天）

| 项目 | 内容 |
|------|------|
| 目标 | 创建可运行的 Android 空壳项目 |
| 输入 | 无 |
| 输出 | Android Studio 项目骨架 |

**实施步骤**：
1. 创建 Android Studio 项目，minSdk 26，targetSdk 34
2. 配置 Gradle (Kotlin DSL)，启用 ViewBinding
3. 创建基础 Activity + WebView 布局
4. 配置 AndroidManifest.xml：INTERNET 权限、VpnService 声明

**关键文件清单**：
```
android/
├── build.gradle.kts
├── app/
│   ├── build.gradle.kts
│   ├── src/main/
│   │   ├── AndroidManifest.xml
│   │   ├── java/com/easytier/eui/
│   │   │   ├── MainActivity.kt
│   │   │   └── EasyTierVpnService.kt      # 空壳
│   │   └── res/
│   │       └── layout/
│   │           └── activity_main.xml
```

**验证标准**：
- [ ] 项目在 Android Studio 中编译通过
- [ ] 在模拟器/真机上可运行空白 Activity
- [ ] WebView 可加载 `about:blank`

---

### Task 0.2：集成 Chaquopy 嵌入式 Python（1 天）

| 项目 | 内容 |
|------|------|
| 目标 | 在 Android 上成功运行 Python 代码 |
| 输入 | Task 0.1 项目骨架 |
| 输出 | Python 代码可在 Android 上执行 |

**Chaquopy 配置**：
```kotlin
// app/build.gradle.kts
plugins {
    id("com.chaquo.python") version "16.0.0"
}

android {
    defaultConfig {
        ndk { abiFilters += listOf("arm64-v8a", "armeabi-v7a") }
        python {
            version = "3.12"
            pip {
                install("tomlkit")
                install("requests")
                install("dnspython")
                // psutil 需要特殊处理，见 Task 2.2
            }
        }
    }
}
```

**实施步骤**：
1. 在 `app/build.gradle.kts` 中添加 Chaquopy 插件
2. 配置 `python { version "3.12" }`
3. 将现有 backend 代码放入 `app/src/main/python/` 目录
4. 在 `requirements-base.txt` 中添加依赖
5. 编写验证脚本：`Python.getInstance().getModule("test").callAttr("hello")`

**验证标准**：
- [ ] `import tomlkit` 成功
- [ ] `import requests` 成功
- [ ] `import dnspython` 成功
- [ ] Python 文件读写正常（Android 沙箱路径）

---

### Task 0.3：WebView 加载前端验证（0.5 天）

| 项目 | 内容 |
|------|------|
| 目标 | 验证 Vue 3 前端在 WebView 中正常渲染 |
| 输入 | Task 0.1 项目骨架 + `frontend/dist/` |
| 输出 | WebView 正常显示前端页面 |

**WebView 关键配置**：
```kotlin
webView.settings.apply {
    javaScriptEnabled = true
    domStorageEnabled = true
    allowFileAccess = true
    mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
}
webView.loadUrl("file:///android_asset/frontend/index.html")
```

**实施步骤**：
1. 将 `frontend/dist/` 放入 `app/src/main/assets/frontend/`
2. 配置 WebView：启用 JS、DOM Storage、跨域
3. 验证 Varlet UI 组件渲染、暗色模式、移动端布局

**验证标准**：
- [ ] 首页正常渲染
- [ ] 节点列表页面可用
- [ ] 配置页面可用
- [ ] 移动端布局正确（`@media` 断点生效）
- [ ] 暗色模式切换正常

---

### Task 0.4：本地 HTTP Server 通信验证（1 天）

| 项目 | 内容 |
|------|------|
| 目标 | Python HTTP Server 与 WebView 前端通信验证 |
| 输入 | Task 0.2 + 0.3 |
| 输出 | 前后端通信链路打通 |

**实施步骤**：
1. 在 Python 中启动 HTTP Server 替代 CGI 模式
2. 动态分配端口，通过 JS Interface 传给 WebView
3. 前端 API 请求指向 `http://127.0.0.1:{port}/api/...`
4. 验证一个完整 API 调用链路

**验证标准**：
- [ ] Python HTTP Server 启动成功
- [ ] 前端成功调用 `/api/configs/list_config_files`
- [ ] JSON 响应正确解析
- [ ] 错误处理正常

---

## 四、Phase 1：Rust FFI 编译与集成（7 天）

### Task 1.1：拉取 EasyTier 源码并分析（1 天）

| 项目 | 内容 |
|------|------|
| 目标 | 理解 EasyTier 内部架构，确定 FFI 边界 |
| 输入 | EasyTier GitHub 仓库 |
| 输出 | FFI 接口设计文档 |

**需分析的关键模块**：
```
EasyTier 源码预期结构：
├── easytier-core/
│   ├── src/
│   │   ├── tun/          # TUN 设备抽象层 ← 需要适配 VpnService fd
│   │   ├── peer/         # P2P 节点管理
│   │   ├── crypto/       # 加密模块
│   │   ├── config/       # 配置解析
│   │   └── main.rs       # 入口（需改造为 lib.rs）
│   └── Cargo.toml
```

**实施步骤**：
1. 拉取 EasyTier 源码，分析 Cargo.toml 结构
2. 识别核心模块：tun 设备、P2P 协议、加密、配置解析
3. 确定需要暴露的 FFI 函数列表
4. 分析 TUN 设备读写接口，规划 VpnService fd 适配方案

**验证标准**：
- [ ] 源码可在本地 `cargo build` 通过
- [ ] 明确 TUN 设备抽象接口
- [ ] 明确需要暴露为 FFI 的核心函数列表

---

### Task 1.2：设计 C ABI 接口（1 天）

| 项目 | 内容 |
|------|------|
| 目标 | 定义 Rust FFI 对外暴露的 C ABI 函数 |
| 输入 | Task 1.1 分析结果 |
| 输出 | C ABI 接口定义 |

**C ABI 接口定义**：

```c
// easytier_ffi.h — 对外暴露的 C 接口

// === 生命周期管理 ===

// 初始化 EasyTier 运行时，传入 JSON 配置字符串
// 返回 0 成功，-1 失败（通过 et_last_error 获取错误信息）
int32_t et_init(const char* config_json);

// 启动组网服务，vpn_fd 为 Android VpnService 提供的文件描述符
// 返回 0 成功，-1 失败
int32_t et_start(int32_t vpn_fd);

// 停止组网服务
// 返回 0 成功，-1 失败
int32_t et_stop(void);

// 获取最后一次错误信息，返回字符串（调用方需通过 et_free_string 释放）
char* et_last_error(void);
void et_free_string(char* s);

// === 状态查询 ===

// 获取运行状态 JSON
// {"running": true, "peers": [...], "uptime": 1234, ...}
char* et_get_status(void);

// 获取当前配置 JSON
char* et_get_config(void);

// === CLI 功能替代 ===

// 执行 CLI 命令（替代 easytier-cli 子进程调用）
// cmd_json: {"action": "peer_list"|"route_list"|"service_status", ...}
// 返回 JSON 结果
char* et_exec_cli(const char* cmd_json);

// === 版本信息 ===
char* et_get_version(void);
```

**设计原则**：
- 所有字符串参数使用 JSON，保持与 Python 后端一致
- 返回字符串由调用方通过 `et_free_string` 释放，避免内存泄漏
- 每个函数返回明确的错误码，错误详情通过 `et_last_error` 获取
- 接口设计覆盖 services.py 和 et_core.py 的所有调用

**验证标准**：
- [ ] 接口覆盖所有 Backend 对 easytier-core/cli 的调用
- [ ] 接口与 Python Backend 的 JSON 数据格式兼容
- [ ] 内存管理方案明确（谁分配谁释放）

---

### Task 1.3：修改 EasyTier 源码为 FFI 库（3 天）

| 项目 | 内容 |
|------|------|
| 目标 | 编译出 `libeasytier.so` 共享库 |
| 输入 | EasyTier 源码 + Task 1.2 接口设计 |
| 输出 | `libeasytier.so` (arm64-v8a, armeabi-v7a) |

**改动清单**：

| 文件 | 改动内容 | 工作量 |
|------|---------|--------|
| `Cargo.toml` | 添加 `[lib]` 段，`crate-type = ["cdylib"]`；添加 `jni` 依赖 | 0.2 天 |
| 新建 `src/lib.rs` | FFI 入口文件，实现所有 `#[no_mangle] extern "C"` 函数 | 1 天 |
| `src/tun/` 适配 | 新增 `TunFd` 实现：接受外部 fd 而非打开 `/dev/tun` | 1 天 |
| 全局状态管理 | 使用 `OnceLock<Mutex<GlobalState>>` 管理单例运行时 | 0.5 天 |
| 构建脚本 | `cargo-ndk` 配置，支持 arm64-v8a / armeabi-v7a | 0.3 天 |

**TUN 适配核心逻辑**：
```rust
// src/tun/tun_fd.rs — 新增文件
// Android 上不使用 /dev/tun，而是使用 VpnService 传入的 fd

pub struct TunFd {
    fd: RawFd,  // 来自 VpnService.establish().fd
}

impl TunFd {
    pub fn new(fd: RawFd) -> Self {
        TunFd { fd }
    }
    
    pub fn read(&self, buf: &mut [u8]) -> io::Result<usize> {
        unsafe {
            let n = libc::read(self.fd, buf.as_mut_ptr() as *mut c_void, buf.len());
            if n < 0 { Err(io::Error::last_os_error()) } else { Ok(n as usize) }
        }
    }
    
    pub fn write(&self, buf: &[u8]) -> io::Result<usize> {
        unsafe {
            let n = libc::write(self.fd, buf.as_ptr() as *const c_void, buf.len());
            if n < 0 { Err(io::Error::last_os_error()) } else { Ok(n as usize) }
        }
    }
}
```

**实施步骤**：
1. Fork EasyTier 仓库，创建 `android-ffi` 分支
2. 修改 Cargo.toml 添加 `[lib]` 段和 `crate-type = ["cdylib"]`
3. 新建 `src/lib.rs` 实现所有 FFI 函数
4. 新增 `src/tun/tun_fd.rs` 实现基于 fd 的 TUN 设备
5. 实现全局状态管理（单例模式）
6. 配置 cargo-ndk 交叉编译

**验证标准**：
- [ ] `cargo ndk --target arm64-v8a build --release` 成功
- [ ] `libeasytier.so` 文件生成，大小约 4-8 MB
- [ ] `nm -D libeasytier.so | grep et_init` 确认符号导出
- [ ] 在 Android 模拟器中加载 .so 并调用 `et_get_version()` 成功

---

### Task 1.4：JNI 桥接层编写（2 天）

| 项目 | 内容 |
|------|------|
| 目标 | Kotlin 层可以调用 Rust FFI 函数 |
| 输入 | Task 1.3 `libeasytier.so` |
| 输出 | RustBridge.kt 封装类 |

**Kotlin 封装类**：
```kotlin
// RustBridge.kt
object RustBridge {
    init {
        System.loadLibrary("easytier")
    }
    
    external fun init(configJson: String): Int
    external fun start(vpnFd: Int): Int
    external fun stop(): Int
    external fun getStatus(): String
    external fun execCli(cmdJson: String): String
    external fun getVersion(): String
    external fun lastError(): String
}
```

**JNI 函数命名规则**（Rust 侧）：
```rust
// 包名 com.easytier.eui.RustBridge → JNI 函数名
#[no_mangle]
pub extern "system" fn Java_com_easytier_eui_RustBridge_init(
    _env: JNIEnv, _class: JClass, config_json: JString
) -> jint { ... }
```

**验证标准**：
- [ ] `RustBridge.getVersion()` 返回正确版本号
- [ ] `RustBridge.init(configJson)` 返回 0
- [ ] `RustBridge.start(vpnFd)` 返回 0
- [ ] `RustBridge.stop()` 正常关闭

---

## 五、Phase 2：Backend 适配（7 天）

### Task 2.1：CGI 模式 → HTTP Server 改造（1.5 天）

| 项目 | 内容 |
|------|------|
| 目标 | 替换 CGI 模式为可独立运行的 HTTP Server |
| 输入 | 现有 dispatcher.py |
| 输出 | 新增 android_server.py，复用现有 dispatcher |

**核心改造说明**：现有 dispatcher 的 `http_handle()` 函数已经处理了完整的路由逻辑（解析 URL → 定位 module/function → 调用 → 返回 HttpResponse），只需把 CGI 的 stdin/stdout 替换为 HTTP Server 的 request/response。

**新增代码**：
```python
# 新增 android_server.py（约 80 行）
from http.server import HTTPServer, BaseHTTPRequestHandler
from http_dispatcher.dispatcher import http_handle

class AndroidHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle('GET')
    
    def do_POST(self):
        self._handle('POST')
    
    def _handle(self, method):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        path = self.path
        query = ''
        if '?' in path:
            path, query = path.split('?', 1)
        
        try:
            response = http_handle(
                request_uri=path,
                method=method,
                query_string=query,
                request_body=body,
                cgi_module=False
            )
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.body_bytes())
        except Exception as e:
            self.send_response(500)
            self.end_headers()

def start_server(port: int = 0) -> int:
    server = HTTPServer(('127.0.0.1', port), AndroidHTTPHandler)
    actual_port = server.server_port
    import threading
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return actual_port
```

**需要修改的现有代码**：
- `dispatcher.py`：`cgi_module=False` 时返回 `HttpResponse` 对象而非调用 `output_cgi()`
- `index.cgi`：保持不变，PC 端仍用 CGI

**验证标准**：
- [ ] `curl http://127.0.0.1:{port}/api/configs/list_config_files` 返回 JSON
- [ ] 前端通过 WebView 调用 API 成功

---

### Task 2.2：psutil 替换方案（1 天）

| 项目 | 内容 |
|------|------|
| 目标 | 替代 psutil 在 Android 上的不可用功能 |
| 输入 | 现有 backend 中 psutil 使用点 |
| 输出 | 新增 process_util_android.py |

**psutil 在 Backend 中的使用点分析**：

| 位置 | 用途 | 替代方案 |
|------|------|---------|
| process_util.py | 进程检测（pid_exists） | 改用 `os.kill(pid, 0)` |
| process_util.py | 进程管理（Process.terminate） | Rust FFI 提供 `et_stop()` |
| monitor.py | CPU/内存监控 | Kotlin 通过 ActivityManager 获取 |

**替代实现**：
```python
# utils/process_util_android.py（新增）
import os, platform

IS_ANDROID = hasattr(platform, 'android_ver')

def pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
```

**验证标准**：
- [ ] `pid_exists(12345)` 行为正确
- [ ] Android 环境检测 `IS_ANDROID` 正确
- [ ] 移除 `import psutil` 后所有测试通过

---

### Task 2.3：et_bridge 模块 — subprocess → FFI 替换（2 天）

| 项目 | 内容 |
|------|------|
| 目标 | 将所有 subprocess 调用 easytier-core/cli 替换为 Rust FFI |
| 输入 | Task 1.4 RustBridge.kt + 现有 backend 代码 |
| 输出 | 新增 utils/et_bridge.py |

**需要替换的调用点**：

| 文件 | 函数 | 原调用方式 | 新调用方式 |
|------|------|-----------|-----------|
| services.py | _get_process_manager | subprocess.Popen | et_bridge.start() |
| services.py | stop | process.terminate() | et_bridge.stop() |
| services.py | _system_service_start | easytier-cli service start | et_bridge.exec_cli({...}) |
| services.py | _system_service_stop | easytier-cli service stop | et_bridge.exec_cli({...}) |
| et_core.py | install | --version 查询 | et_bridge.get_version() |
| check_peers.py | check_peer_with_easytier | subprocess.Popen | et_bridge.check_peer(url) |

**Python 侧 FFI 封装**：
```python
# utils/et_bridge.py（新增，约 150 行）
import json, platform

IS_ANDROID = hasattr(platform, 'android_ver')

if IS_ANDROID:
    from java import jclass
    _RustBridge = jclass('com.easytier.eui.RustBridge')
else:
    _RustBridge = None

class EtBridge:
    def start(self, config: dict, vpn_fd: int = -1) -> int:
        if IS_ANDROID:
            config_json = json.dumps(config)
            rc = _RustBridge.init(config_json)
            if rc != 0:
                raise RuntimeError(f"初始化失败: {_RustBridge.lastError()}")
            return _RustBridge.start(vpn_fd)
        else:
            return self._start_pc(config)
    
    def stop(self) -> int:
        if IS_ANDROID:
            return _RustBridge.stop()
        else:
            return self._stop_pc()
    
    def get_status(self) -> dict:
        if IS_ANDROID:
            return json.loads(_RustBridge.getStatus())
        else:
            return self._get_status_pc()
    
    def exec_cli(self, action: str, **params) -> dict:
        cmd = json.dumps({"action": action, **params})
        if IS_ANDROID:
            return json.loads(_RustBridge.execCli(cmd))
        else:
            return self._exec_cli_pc(action, **params)
    
    def get_version(self) -> str:
        if IS_ANDROID:
            return _RustBridge.getVersion()
        else:
            return self._get_version_pc()

et_bridge = EtBridge()
```

**改造策略**：通过 `IS_ANDROID` 条件保持 PC 端不变。

**验证标准**：
- [ ] `et_bridge.get_version()` 返回正确版本
- [ ] `et_bridge.start(config)` 成功启动
- [ ] `et_bridge.get_status()` 返回 JSON
- [ ] `et_bridge.stop()` 成功停止
- [ ] PC 端逻辑不受影响

---

### Task 2.4：文件路径适配（0.5 天）

| 项目 | 内容 |
|------|------|
| 目标 | 适配 Android 沙箱文件系统 |
| 输入 | 现有 run_configs.py |
| 输出 | 修改后的路径配置 |

**路径映射**：

| 原路径（Linux） | Android 路径 | 说明 |
|----------------|-------------|------|
| /var/apps/EasyTier-EUI/ | context.filesDir | 应用私有目录 |
| {data_dir}/config/ | {filesDir}/config/ | 配置文件 |
| {data_dir}/logs/ | {filesDir}/logs/ | 日志 |
| FRONTEND_PATH | file:///android_asset/frontend/ | 前端资源 |

```python
# run_configs.py 改动
if IS_ANDROID:
    from java import jclass
    _Context = jclass('com.easytier.eui.MainActivity')
    DATA_DIR = _Context.getFilesDir().getAbsolutePath()
    FRONTEND_PATH = 'file:///android_asset/frontend/'
else:
    DATA_DIR = os.environ.get('DATA_DIR', '/var/apps/EasyTier-EUI')
```

**验证标准**：
- [ ] 配置文件读写正确
- [ ] 日志文件正常写入
- [ ] 前端资源正确加载

---

### Task 2.5：VpnService 完整实现（2 天）

| 项目 | 内容 |
|------|------|
| 目标 | 实现 VPN 开启/关闭/状态管理 |
| 输入 | Task 1.4 RustBridge |
| 输出 | EasyTierVpnService.kt 完整实现 |

**核心实现**：
```kotlin
// EasyTierVpnService.kt
class EasyTierVpnService : VpnService() {
    
    companion object {
        const val ACTION_START = "com.easytier.eui.START_VPN"
        const val ACTION_STOP = "com.easytier.eui.STOP_VPN"
        var isRunning = false; private set
        var vpnFd: Int = -1; private set
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startVpn(intent.getStringExtra("config_json") ?: "{}")
            ACTION_STOP -> stopVpn()
        }
        return START_STICKY
    }
    
    private fun startVpn(configJson: String) {
        val config = JSONObject(configJson)
        val virtualIp = config.optString("ipv4", "10.144.0.1")
        
        val builder = Builder()
            .setSession("EasyTier 组网")
            .setMtu(1400)
            .addAddress(virtualIp, 24)
            .addRoute("0.0.0.0", 0)
            .addDnsServer("223.5.5.5")
            .addDnsServer("8.8.8.8")
            .setBlocking(true)
        
        val vpnInterface = builder.establish()
        vpnFd = vpnInterface?.fd ?: -1
        
        if (vpnFd < 0) { broadcastStatus("error", "VPN 建立失败"); return }
        
        thread {
            val rc = RustBridge.init(configJson)
            if (rc != 0) { broadcastStatus("error", RustBridge.lastError()); return@thread }
            val startRc = RustBridge.start(vpnFd)
            if (startRc == 0) { isRunning = true; broadcastStatus("running") }
            else { broadcastStatus("error", RustBridge.lastError()) }
        }
        
        startForeground(NOTIFICATION_ID, buildNotification())
    }
    
    private fun stopVpn() {
        RustBridge.stop()
        isRunning = false; vpnFd = -1
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf(); broadcastStatus("stopped")
    }
    
    private fun broadcastStatus(status: String, error: String = "") {
        val intent = Intent("com.easytier.eui.VPN_STATUS_CHANGED").apply {
            putExtra("status", status); putExtra("error", error)
        }
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent)
    }
    
    private fun buildNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("EasyTier 组网运行中")
            .setContentText("虚拟网络已连接")
            .setSmallIcon(R.drawable.ic_vpn)
            .setOngoing(true).build()
    }
}
```

**AndroidManifest.xml 配置**：
```xml
<service
    android:name=".EasyTierVpnService"
    android:permission="android.permission.BIND_VPN_SERVICE"
    android:exported="false">
    <intent-filter>
        <action android:name="android.net.VpnService" />
    </intent-filter>
</service>
```

**验证标准**：
- [ ] VPN 权限申请弹窗正常显示
- [ ] 用户授权后 VPN 成功建立
- [ ] 状态栏显示 VPN 图标
- [ ] 前台通知正常显示
- [ ] 停止 VPN 后网络恢复
- [ ] 组网设备间可以 ping 通

---

## 六、Phase 3：联调测试与优化（5 天）

### Task 3.1：前后端完整联调（2 天）

| 测试项 | 覆盖场景 | 优先级 |
|--------|---------|--------|
| 配置管理 | 新建/编辑/删除/导入/导出配置 | P0 |
| 服务管理 | 启动/停止/重启/查看状态 | P0 |
| 节点管理 | 节点列表/检测/添加/公网节点 | P0 |
| 设置功能 | 语言切换/主题切换/代理设置 | P1 |
| 下载功能 | 各平台安装包下载 | P1 |
| 错误处理 | 网络断开/权限拒绝/进程崩溃 | P0 |

**测试矩阵**：

| Android 版本 | 架构 | 测试状态 |
|-------------|------|---------|
| Android 14 (API 34) | arm64-v8a | ☐ |
| Android 13 (API 33) | arm64-v8a | ☐ |
| Android 12 (API 31) | arm64-v8a | ☐ |
| Android 11 (API 30) | armeabi-v7a | ☐ |
| 模拟器 | x86_64 | ☐ |

---

### Task 3.2：性能优化（1.5 天）

| 优化项 | 问题 | 解决方案 |
|--------|------|---------|
| 启动速度 | Python 初始化 3-5s | 预初始化 Python 运行时；延迟加载非关键模块 |
| 内存占用 | 150-250 MB | 使用 __pycache__ 预编译；WebView 独立进程 |
| 电量消耗 | VPN 持续运行耗电 | Rust 层优化轮询间隔；降低心跳频率 |
| APK 体积 | 40-60 MB | ABI 分拆；前端资源压缩；Python 标准库裁剪 |

**Python 启动优化**：
```python
# 预编译 Python 模块（构建时执行）
import compileall
compileall.compile_dir('app/src/main/python', force=True)
```

**WebView 独立进程**：
```xml
<!-- AndroidManifest.xml -->
<activity android:name=".MainActivity" android:process=":webview" />
```

**验证标准**：
- [ ] 冷启动时间 < 5 秒
- [ ] 热启动时间 < 2 秒
- [ ] 空闲内存占用 < 150 MB
- [ ] APK 体积 < 50 MB

---

### Task 3.3：稳定性测试（1.5 天）

| 测试场景 | 操作 | 预期结果 |
|---------|------|---------|
| 长时间运行 | VPN 持续运行 24h | 无崩溃、无内存泄漏 |
| 前后台切换 | 反复切换 50 次 | VPN 状态保持 |
| 网络切换 | WiFi ↔ 移动数据 | 自动重连 |
| 低内存 | 模拟低内存场景 | 前台服务不被杀死 |
| 异常恢复 | 强制杀死进程 | 重启后恢复 VPN |
| 并发操作 | 快速点击启动/停止 | 状态一致 |

---

## 七、Phase 4：发布准备（3 天）

### Task 4.1：构建脚本与 CI（1.5 天）

| 项目 | 内容 |
|------|------|
| 目标 | 自动化构建流程 |
| 输出 | build_android.sh + GitHub Actions |

**构建流程**：
```bash
#!/bin/bash
# build_android.sh

# 1. 编译前端
cd frontend && npm run build && cd ..

# 2. 复制前端到 Android assets
cp -r frontend/dist/* android/app/src/main/assets/frontend/

# 3. 编译 Rust FFI（各架构）
cd easytier-core
cargo ndk --target arm64-v8a --platform 26 build --release
cargo ndk --target armeabi-v7a --platform 26 build --release
cd ..

# 4. 复制 .so 到 Android jniLibs
cp target/aarch64-linux-android/release/libeasytier.so \
   android/app/src/main/jniLibs/arm64-v8a/
cp target/armv7-linux-androideabi/release/libeasytier.so \
   android/app/src/main/jniLibs/armeabi-v7a/

# 5. 编译 APK
cd android && ./gradlew assembleRelease && cd ..

# 6. 签名
apksigner sign --ks release.jks android/app/build/outputs/apk/release/app-release.apk
```

---

### Task 4.2：版本号与更新机制（0.5 天）

| 项目 | 内容 |
|------|------|
| versionCode | 跟随 EasyTier-EUI 版本号 |
| versionName | 1.2.0-android |
| 更新检查 | 复用现有 GitHub Release 检查逻辑 |

---

### Task 4.3：文档与发布（1 天）

- 用户使用文档（VPN 权限说明、配置导入）
- 开发者文档（架构说明、构建流程）
- APK 发布到 GitHub Release

---

## 八、风险与缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Chaquopy 与最新 Android 不兼容 | 中 | 高 | 备选：Termux 或 BeeWare 方案 |
| psutil 无法完全替代 | 中 | 中 | Phase 0 提前验证，必要时用 Kotlin 实现 |
| EasyTier TUN 适配 VpnService fd 有坑 | 高 | 高 | 提前做 POC 验证 |
| Python 性能不满足实时网络要求 | 低 | 中 | 核心网络路径在 Rust 层，Python 仅做管理 API |
| Google Play 审核拒绝 | 中 | 低 | 优先通过 GitHub Release 分发 |

---

## 九、文件清单总览

```
android/
├── build.gradle.kts                          # 新增
├── settings.gradle.kts                       # 新增
├── app/
│   ├── build.gradle.kts                      # 新增（Chaquopy 配置）
│   ├── src/main/
│   │   ├── AndroidManifest.xml               # 新增
│   │   ├── assets/
│   │   │   └── frontend/                     # 复制自 frontend/dist/
│   │   ├── java/com/easytier/eui/
│   │   │   ├── MainActivity.kt               # 新增
│   │   │   ├── EasyTierVpnService.kt         # 新增
│   │   │   ├── RustBridge.kt                 # 新增
│   │   │   └── PythonServer.kt              # 新增
│   │   ├── jniLibs/
│   │   │   ├── arm64-v8a/libeasytier.so      # Rust 编译产物
│   │   │   └── armeabi-v7a/libeasytier.so    # Rust 编译产物
│   │   ├── python/                           # 复制自 app/backend/
│   │   │   ├── android_server.py             # 新增（CGI→HTTP）
│   │   │   ├── http_dispatcher/
│   │   │   │   └── dispatcher.py             # 修改（非CGI模式）
│   │   │   ├── actions/
│   │   │   │   ├── services.py               # 修改（subprocess→FFI）
│   │   │   │   ├── et_core.py                # 修改（subprocess→FFI）
│   │   │   │   ├── configs.py                # 复用
│   │   │   │   ├── peers.py                  # 复用
│   │   │   │   ├── settings.py               # 复用
│   │   │   │   ├── monitor.py                # 复用
│   │   │   │   └── et_eui.py                 # 复用
│   │   │   ├── utils/
│   │   │   │   ├── et_bridge.py              # 新增（FFI桥接）
│   │   │   │   ├── process_util_android.py   # 新增（替代psutil）
│   │   │   │   ├── run_configs.py            # 修改（路径适配）
│   │   │   │   └── ...                       # 其余复用
│   │   │   ├── locales/                      # 完全复用
│   │   │   └── requirements-base.txt         # 修改（移除psutil?）
│   │   └── res/
│   │       └── values/strings.xml            # 新增

easytier-core/                                 # EasyTier 源码（需 fork）
├── Cargo.toml                                # 修改（添加cdylib）
├── src/
│   ├── lib.rs                                # 新增（FFI入口）
│   ├── tun/
│   │   └── tun_fd.rs                         # 新增（VpnService fd适配）
│   └── ...                                   # 其余代码

build_android.sh                              # 新增（构建脚本）
```

---

## 十、工时汇总

| Phase | 任务 | 人天 |
|-------|------|------|
| **P0** | **环境搭建与验证** | **3** |
| P0.1 | Android 项目初始化 | 0.5 |
| P0.2 | Chaquopy 集成 | 1 |
| P0.3 | WebView 前端验证 | 0.5 |
| P0.4 | HTTP Server 通信验证 | 1 |
| **P1** | **Rust FFI 编译** | **7** |
| P1.1 | EasyTier 源码分析 | 1 |
| P1.2 | C ABI 接口设计 | 1 |
| P1.3 | FFI 库编译 | 3 |
| P1.4 | JNI 桥接层 | 2 |
| **P2** | **Backend 适配** | **7** |
| P2.1 | CGI→HTTP Server | 1.5 |
| P2.2 | psutil 替换 | 1 |
| P2.3 | et_bridge 模块 | 2 |
| P2.4 | 文件路径适配 | 0.5 |
| P2.5 | VpnService 实现 | 2 |
| **P3** | **联调测试优化** | **5** |
| P3.1 | 完整联调 | 2 |
| P3.2 | 性能优化 | 1.5 |
| P3.3 | 稳定性测试 | 1.5 |
| **P4** | **发布** | **3** |
| P4.1 | 构建脚本+CI | 1.5 |
| P4.2 | 版本管理 | 0.5 |
| P4.3 | 文档发布 | 1 |
| | | |
| **总计** | | **25 人天** |
| **加缓冲 20%** | | **~30 人天** |

---

## 十一、方案对比速查

| 维度 | 本方案（WebView+Python+FFI） | UniApp 方案 | Flutter 方案 |
|------|---------------------------|-------------|-------------|
| 前端复用 | 极高（零改动） | 高（迁移适配） | 零（重写） |
| 后端复用 | 极高（90%+） | 零（重写） | 零（重写） |
| 开发工时 | ~30 人天 | ~60-80 人天 | ~80+ 人天 |
| APK 体积 | 40-60 MB | 15-25 MB | 20-30 MB |
| 内存占用 | 150-250 MB | 80-120 MB | 100-150 MB |
| 启动速度 | 3-5s | 1-2s | 1-2s |
| 技术风险 | 中 | 低 | 低 |
| 长期维护 | 复杂 | 简单 | 中等 |
| 跨平台扩展 | 仅 Android | iOS/鸿蒙/小程序 | iOS/Desktop |