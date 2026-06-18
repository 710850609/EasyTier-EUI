#!/bin/bash
# 启动 EasyTier-EUI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/EasyTier-EUI"
PID_FILE="$SCRIPT_DIR/data/server.pid"
LOG_FILE="$SCRIPT_DIR/logs/app.log"

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/data"

# 输出同时写入终端和日志文件
exec > >(tee -a "$LOG_FILE") 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') === start.sh 执行 ==="

# 检查可执行文件
if [ ! -x "$EXECUTABLE" ]; then
    echo "错误：找不到可执行文件 $EXECUTABLE" >&2
    [ -t 0 ] && read -p "按 Enter 退出..."
    exit 1
fi

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if sudo kill -0 "$PID" 2>/dev/null; then
        echo "EasyTier-EUI 已在运行 (PID: $PID)"
        [ -t 0 ] && read -p "按 Enter 退出..."
        exit 1
    fi
    sudo rm -f "$PID_FILE"
fi

# 启动（保留日志，获取真实 PID）
echo "正在尝试启动 EasyTier-EUI..."

# 不使用 sudo 启动，尽量使用普通账户模式启动，尝试自动打开浏览器。把真实 PID 写入文件
bash -c "
  nohup '$EXECUTABLE' >> /dev/null 2>&1 &
"

# 检查是否真的启动了
echo "等待 EasyTier-EUI 启动 (3 秒)"
sleep 3
if [ -f "$PID_FILE" ]; then
    REAL_PID=$(cat "$PID_FILE")
    echo "获取到的 PID: $REAL_PID"
    if sudo kill -0 "$REAL_PID" 2>/dev/null; then
        echo "EasyTier-EUI 已启动，PID: $REAL_PID"
        echo "启动信息：可点击URL跳浏览器访问，或是手机扫描二维码访问"
    else
        echo "警告：程序可能启动失败"
    fi
else
    echo "错误：未能获取进程 PID"
fi

# 显示日志
if [ -f "$LOG_FILE" ]; then
    echo ""
    echo "--- 启动日志 ---"
    tail -20 "$LOG_FILE"
fi

echo ""
echo "程序已在后台运行，关闭此窗口不影响服务。关闭请运行 stop.sh"
[ -t 0 ] && read -p "按 Enter 键关闭窗口..."