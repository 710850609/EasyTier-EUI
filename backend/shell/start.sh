#!/bin/bash
# 启动 EasyTier-EUI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/EasyTier-EUI"
PID_FILE="$SCRIPT_DIR/data/server.pid"
LOG_FILE="$SCRIPT_DIR/logs/app.log"
SCRIPT_NAME="start.sh"

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/data"

# 统一日志输出（同时输出到终端和日志文件）
log() {
    local msg="$(date '+%Y-%m-%d %H:%M:%S') - [ $SCRIPT_NAME ] - $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log "执行"

# 检查可执行文件
if [ ! -x "$EXECUTABLE" ]; then
    log "错误：找不到可执行文件 $EXECUTABLE"
    [ -t 0 ] && read -p "按 Enter 退出..."
    exit 1
fi

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if sudo kill -0 "$PID" 2>/dev/null; then
        log "EasyTier-EUI 已在运行 (PID: $PID)"
        [ -t 0 ] && read -p "按 Enter 退出..."
        exit 1
    fi
    sudo rm -f "$PID_FILE"
fi

# 启动 EasyTier-EUI（前台等待密码确认后，再后台化）
log "正在尝试启动 EasyTier-EUI..."
"$EXECUTABLE" >> /dev/null 2>&1 &
LAUNCH_PID=$!

# 等待 EasyTier-EUI 完成提权（内部弹密码框，确认后原进程退出，新进程写 PID 文件）
log "等待 EasyTier-EUI 启动..."
WAIT_SEC=0
while [ $WAIT_SEC -lt 30 ]; do
    if [ -f "$PID_FILE" ]; then
        break
    fi
    sleep 1
    WAIT_SEC=$((WAIT_SEC + 1))
    log "等待 EasyTier-EUI 启动 (已等待 $WAIT_SEC 秒)"
done

if [ -f "$PID_FILE" ]; then
    REAL_PID=$(cat "$PID_FILE")
    if sudo kill -0 "$REAL_PID" 2>/dev/null; then
        log "EasyTier-EUI 已启动，PID: $REAL_PID"
        [ -t 0 ] && echo "启动信息：可点击URL跳浏览器访问，或是手机扫描二维码访问"
    else
        log "警告：程序可能启动失败"
    fi
else
    log "错误：未能获取进程 PID"
fi

# 显示日志（只在交互终端）
if [ -t 0 ] && [ -f "$LOG_FILE" ]; then
    echo ""
    echo "--- 启动日志 ---"
    tail -20 "$LOG_FILE"
fi

# 终端提示（只在交互终端）
if [ -t 0 ]; then
    echo ""
    echo "程序已在后台运行，关闭此窗口不影响服务。关闭请运行 stop.sh"
    read -p "按 Enter 键关闭窗口..."
fi