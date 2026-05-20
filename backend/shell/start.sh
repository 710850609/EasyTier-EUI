#!/bin/sh
# 启动 EasyTier-Lite

# 获取脚本所在目录（绝对路径）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/EasyTier-Lite"
PID_FILE="$SCRIPT_DIR/easytier.pid"

# 检查可执行文件是否存在且可执行
if [ ! -x "$EXECUTABLE" ]; then
    echo "错误：找不到可执行文件 $EXECUTABLE" >&2
    exit 1
fi

# 可选：防止重复启动（通过 pid 文件）
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "EasyTier-Lite 似乎已在运行 (PID: $PID)"
        exit 1
    fi
fi

# 后台运行（nohup 防止终端关闭时退出，输出重定向到空）
nohup "$EXECUTABLE" > /dev/null 2>&1 &
PID=$!
echo $PID > "$PID_FILE"
echo "EasyTier-Lite 已启动，PID: $PID"