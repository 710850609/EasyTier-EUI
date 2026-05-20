#!/bin/sh
# 停止 EasyTier-Lite 的所有进程

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/EasyTier-Lite"
PID_FILE="$SCRIPT_DIR/easytier.pid"

# 1. 先用 PID 文件尝试停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "正在停止 PID $PID ..."
        kill "$PID"
        sleep 1
        # 若仍存活，强制杀死
        if kill -0 "$PID" 2>/dev/null; then
            echo "强制停止 PID $PID ..."
            kill -9 "$PID"
        fi
    fi
    rm -f "$PID_FILE"
fi

# 2. 再通过进程名清理残留（兼容有/无 pkill 的环境）
if command -v pkill >/dev/null 2>&1; then
    pkill -f "EasyTier-Lite"
else
    # 回退方案：ps + grep + awk + kill
    PIDS=$(ps -eo pid,args | grep "$EXECUTABLE" | grep -v grep | awk '{print $1}')
    if [ -n "$PIDS" ]; then
        echo "正在停止残留进程: $PIDS"
        kill $PIDS 2>/dev/null
    fi
fi

echo "EasyTier-Lite 已停止"