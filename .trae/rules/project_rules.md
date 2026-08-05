# EasyTier-EUI 项目 AI 约束

## 工具使用约束

### 禁止使用命令行操作
- **禁止** 使用 `RunCommand` 工具执行任何 shell/PowerShell 命令（包括 `git`、`gradlew`、`npm`、`python` 等）
- **禁止** 使用 `CheckCommandStatus`、`StopCommand` 工具
- 所有操作必须通过工具函数完成：`Read`、`Edit`、`Write`、`Glob`、`Grep`、`SearchCodebase`、`LS` 等
- 原因：PyCharm IDE下，是没法得到执行结果

### 文件读写换行符
- 当前项目运行在 **Windows** 系统，读写文件须使用 `\r\n`（CRLF）换行符
- 使用 `Write` 工具时，确保内容换行符为 `\r\n`，否则可能导致写入失败

## 技术栈关键信息

- **Kotlin 版本**: 2.0.0（`String.format()` 已移除，需用字符串插值替代）
- **Python 版本**: 3.12（通过 Chaquopy 17.0.0 嵌入）
- **前端**: Vue 3 + Varlet UI
- **FFI**: Python `ctypes` 调用 `libeasytier_ffi.so`（纯 Python FFI，无 JNI 层）