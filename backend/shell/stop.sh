#!/bin/sh
# 停止 EasyTier-EUI 的所有进程

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/EasyTier-EUI"
PID_FILE="$SCRIPT_DIR/data/server.pid"
LOG_FILE="$SCRIPT_DIR/logs/app.log"
SCRIPT_NAME="stop.sh"
APP_NAME="EasyTier-EUI"

mkdir -p "$SCRIPT_DIR/logs"

# 统一日志输出（同时输出到终端和日志文件）
log() {
    msg="$(date '+%Y-%m-%d %H:%M:%S') - [ $SCRIPT_NAME ] - $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

log "执行"

# 1. 先用 PID 文件尝试停止
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if sudo kill -0 "$PID" 2>/dev/null; then
        # 校验进程名，防止 PID 被其他进程回收导致误杀
        PROC_NAME=$(sudo ps -p "$PID" -o comm= 2>/dev/null || echo "")
        if [ "$PROC_NAME" = "$APP_NAME" ] || [ "$PROC_NAME" = "./$APP_NAME" ]; then
            log "正在停止 PID $PID ..."
            sudo kill "$PID"
            sleep 1
            # 若仍存活，强制杀死
            if sudo kill -0 "$PID" 2>/dev/null; then
                log "强制停止 PID $PID ..."
                sudo kill -9 "$PID"
            fi
        else
            log "PID $PID 已被其他进程回收（进程名=$PROC_NAME），跳过停止"
        fi
    fi
    sudo rm -f "$PID_FILE"
fi

# 2. 再通过进程名清理残留（兼容有/无 pkill 的环境）
if command -v pkill >/dev/null 2>&1; then
    sudo pkill -x "$APP_NAME" 2>/dev/null || true
else
    # 回退方案：ps + grep + awk + kill
    PIDS=$(ps -eo pid,args | grep "$EXECUTABLE" | grep -v grep | awk '{print $1}')
    if [ -n "$PIDS" ]; then
        log "正在停止残留进程: $PIDS"
        sudo kill $PIDS 2>/dev/null
    fi
fi

# 3. 确认进程已全部退出（最多等 5 秒）
WAIT_SEC=0
while pgrep -x "$APP_NAME" > /dev/null 2>&1; do
    if [ $WAIT_SEC -ge 5 ]; then
        break
    fi
    sleep 1
    WAIT_SEC=$((WAIT_SEC + 1))
done

if pgrep -x "$APP_NAME" > /dev/null 2>&1; then
    log "[错误] EasyTier-EUI 仍在运行，停止失败"
else
    log "EasyTier-EUI 已停止"
fi

[ -t 0 ] && read -p "按 Enter 键关闭窗口..."