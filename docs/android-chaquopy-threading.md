# Android Chaquopy 线程安全经验总结

## 核心结论

**Python 原生创建的线程中不能调用 Chaquopy 的 `jclass()` 及任何 Java 对象，会直接触发 native crash（SIGABRT）。**

## 现象

```text
Fatal Python error: Aborted

Current thread 0x0000007898fdc400 (most recent call first):
  File ".../actions/et_eui.py", line 87 in _do_update
  File ".../utils/async_task.py", line 63 in _run
  File ".../utils/async_task.py", line 78 in start
```

`_do_update` 通过 `task.start()` 运行在 Python 原生 `threading.Thread(daemon=True)` 创建的线程中，其中调用 `from java import jclass; jclass(...)` 直接导致进程 abort。

## 原因分析

### 为什么有的线程能调 jclass，有的不能？

| 线程来源 | 能否调 jclass | 原因 |
|----------|:------------:|------|
| Python 主线程 | ✅ | Chaquopy 初始化时已 attach JVM |
| Chaquopy HTTP handler 线程 | ✅ | Chaquopy 内部创建，已自动 attach JVM |
| `@JavascriptInterface` 回调 | ✅ | WebView 回调，天然在主线程 |
| **Python `threading.Thread` 创建的线程** | **❌** | **未 attach JVM，调用 JNI 直接 crash** |

关键区别：**线程是否由 Chaquopy 基础设施创建**。Chaquopy 管理的线程会自动调用 `AttachCurrentThread` 绑定 JVM，而 Python 原生 `threading.Thread` 不会。

### 为什么 try/except 没捕获到异常？

`Fatal Python error: Aborted` 是 **native 层 SIGABRT 信号**，不是 Python 异常。Python 的 `try/except Exception` 无法捕获 native crash，进程直接终止。

## 解决方案

### 方案一：前端兜底（推荐，本项目采用）

Python 后台线程只做纯 Python 操作（下载、解压等），需要与 Java 交互时，通过 task 状态传递数据，由前端轮询后通过 `AndroidBridge` 触发。

```
Python daemon 线程                  HTTP handler 线程             前端 (WebView)
     │                                  │                          │
     │  下载完成，存 file_path           │                          │
     │  task.set_completed()            │                          │
     │                                  │                          │
     │                                  │  get_update_progress()   │
     │                                  │─────────────────────────>│
     │                                  │  {status: 1, file_path}  │
     │                                  │<─────────────────────────│
     │                                  │                          │
     │                                  │        AndroidBridge     │
     │                                  │     .installApk(path)    │
     │                                  │<─────────────────────────│
     │                                  │                          │
     │                                  │  @JavascriptInterface    │
     │                                  │  在主线程调 installApk   │
```

```python
# ❌ 错误：在 daemon 线程中调 Java
elif run_configs.IS_ANDROID:
    from java import jclass                      # ← 这里 crash！
    MainActivity = jclass(run_configs.ANDROID_MAIN_ACTIVITY)
    manager = MainActivity.getEasyTierManager()
    manager.installApk(download_file)

# ✅ 正确：只存数据，不碰 Java
elif run_configs.IS_ANDROID:
    task.set_file_path(download_file)
    task.set_completed(get_message('update.completed'))
```

```kotlin
// AndroidBridge 中新增方法，由前端调用
@JavascriptInterface
fun installApk(filePath: String) {
    runOnUiThread {
        easyTierManager?.installApk(filePath)
    }
}
```

```javascript
// 前端轮询到完成时，触发安装
if (progress.status === 1 && progress.file_path) {
    if (window.AndroidBridge && window.AndroidBridge.installApk) {
        window.AndroidBridge.installApk(progress.file_path)
    }
}
```

### 方案二：使用 threading 模块时手动 attach（不推荐）

理论上可以通过 `java.lang.System` 等方式手动 attach，但 Chaquopy 未暴露相关 API，且容易引入其他问题，不推荐。

### 方案三：避免使用 Python 原生线程

如果业务逻辑必须在后台线程中调用 Java，可以考虑：
- 使用 Chaquopy 提供的异步机制
- 将 Java 调用逻辑放在 HTTP handler 中（HTTP handler 线程是安全的）
- 通过 `@JavascriptInterface` 由前端驱动

## 检查清单

当需要在 Python 中调用 Java 时，确认以下问题：

- [ ] 当前线程是否由 Chaquopy 管理？（Python 主线程、HTTP handler 线程）
- [ ] 是否使用了 `threading.Thread` 创建线程？
- [ ] 是否可以通过 task 状态 + 前端 `AndroidBridge` 替代？
- [ ] 如果必须后台调 Java，是否已确保线程已 attach JVM？

## 相关文件

- [et_eui.py](file:///F:/git-space/EasyTier-EUI/backend/actions/et_eui.py) — 自更新流程（已修复）
- [ffi_adapter.py](file:///F:/git-space/EasyTier-EUI/backend/et_adapters/ffi_adapter.py) — VPN 启动时的 Java 调用（HTTP handler 线程，安全）
- [async_task.py](file:///F:/git-space/EasyTier-EUI/backend/utils/async_task.py) — `UpdateTask` / `AsyncTask.start()` 创建 daemon 线程
- [MainActivity.kt](file:///F:/git-space/EasyTier-EUI/android/app/src/main/java/com/github/u710850609/easytiereui/MainActivity.kt) — `AndroidBridge` 提供前端调用接口