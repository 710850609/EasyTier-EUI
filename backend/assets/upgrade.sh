#!/bin/bash
# EasyTier-EUI 升级脚本
# 由主进程以独立进程组启动，负责等待旧进程退出 → 替换二进制 → 重启

set -e

if [ -z "$1" ]; then
    echo "用法: $0 \"安装路径\""
    exit 1
fi

APP_DIR="$1"
UPDATE_DIR="$APP_DIR/_update"
APP_NAME="EasyTier-EUI"
LOG_DIR="$APP_DIR/logs"
SCRIPT_NAME="upgrade.sh"
SCRIPT_PATH="$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")"

mkdir -p "$LOG_DIR"

# 统一日志输出（同时输出到终端和日志文件）
log() {
    local msg="$(date '+%Y-%m-%d %H:%M:%S') - [$SCRIPT_NAME] - $*"
    echo "$msg"
    echo "$msg" >> "$LOG_DIR/app.log"
}

log "执行"

# 等待旧进程完全退出（最多等 10 秒）
WAIT_SEC=0
while pgrep -x "$APP_NAME" > /dev/null 2>&1; do
    if [ $WAIT_SEC -ge 10 ]; then
        log "等待超时，强制终止旧进程"
        killall -9 "$APP_NAME" > /dev/null 2>&1 || true
        sleep 2
        break
    fi
    log "等待旧进程退出... ($WAIT_SEC 秒)"
    sleep 1
    WAIT_SEC=$((WAIT_SEC + 1))
done

log "旧进程已退出，开始替换文件"

# 替换二进制
if [ -f "$UPDATE_DIR/$APP_NAME" ]; then
    mv -f "$UPDATE_DIR/$APP_NAME" "$APP_DIR/$APP_NAME"
    chmod +x "$APP_DIR/$APP_NAME"
    log "二进制已替换"
else
    log "错误: 更新文件不存在 $UPDATE_DIR/$APP_NAME"
    exit 1
fi

# 清理更新目录
rm -rf "$UPDATE_DIR"
log "更新目录已清理"

# 启动
if [[ "$OSTYPE" == "darwin"* ]]; then
    log "在 macOS 上启动..."
    open "$APP_DIR/$APP_NAME"
else
    log "在 Linux 上启动..."
    sudo "$APP_DIR/start.sh" &
    log "启动命令已执行"
fi

log "完成"

# 删除脚本自身
rm -f -- "$SCRIPT_PATH"