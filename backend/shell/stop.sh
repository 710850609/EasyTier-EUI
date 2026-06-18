#!/bin/bash
# 停止 EasyTier-EUI 的所有进程

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/EasyTier-EUI"
PID_FILE="$SCRIPT_DIR/data/server.pid"
LOG_FILE="$SCRIPT_DIR/logs/app.log"

mkdir -p "$SCRIPT_DIR/logs"

# 输出同时写入终端和日志文件
exec > >(tee -a "$LOG_FILE") 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') === stop.sh 执行 ==="

# 1. 先用 PID 文件尝试停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if sudo kill -0 "$PID" 2>/dev/null; then
        echo "正在停止 PID $PID ..."
        sudo kill "$PID"
        sleep 1
        # 若仍存活，强制杀死
        if sudo kill -0 "$PID" 2>/dev/null; then
            echo "强制停止 PID $PID ..."
            sudo kill -9 "$PID"
        fi
    fi
    sudo rm -f "$PID_FILE"
fi

# 2. 再通过进程名清理残留（兼容有/无 pkill 的环境）
if command -v pkill >/dev/null 2>&1; then
    sudo pkill -f "EasyTier-EUI"
else
    # 回退方案：ps + grep + awk + kill
    PIDS=$(ps -eo pid,args | grep "$EXECUTABLE" | grep -v grep | awk '{print $1}')
    if [ -n "$PIDS" ]; then
        echo "正在停止残留进程: $PIDS"
        sudo kill $PIDS 2>/dev/null
    fi
fi

echo "EasyTier-EUI 已停止"
[ -t 0 ] && read -p "按 Enter 键关闭窗口..."