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

mkdir -p "$LOG_DIR"

# 所有输出重定向到日志文件，因为已脱离主进程，没有终端
exec >> "$LOG_DIR/upgrade.log" 2>&1
echo "========================================="
echo "$(date '+%Y-%m-%d %H:%M:%S') 升级脚本启动"
echo "APP_DIR=$APP_DIR"
echo "========================================="

# 等待旧进程完全退出（最多等 5 秒）
WAIT_SEC=0
while pgrep -x "$APP_NAME" > /dev/null 2>&1; do
    if [ $WAIT_SEC -ge 5 ]; then
        echo "等待超时，强制终止旧进程"
        killall -9 "$APP_NAME" > /dev/null 2>&1 || true
        sleep 2
        break
    fi
    echo "等待旧进程退出... ($WAIT_SEC 秒)"
    sleep 1
    WAIT_SEC=$((WAIT_SEC + 1))
done

echo "旧进程已退出，开始替换文件"

# 替换二进制
if [ -f "$UPDATE_DIR/$APP_NAME" ]; then
    mv -f "$UPDATE_DIR/$APP_NAME" "$APP_DIR/$APP_NAME"
    chmod +x "$APP_DIR/$APP_NAME"
    echo "二进制已替换"
else
    echo "错误: 更新文件不存在 $UPDATE_DIR/$APP_NAME"
    exit 1
fi

# 清理更新目录
rm -rf "$UPDATE_DIR"
echo "更新目录已清理"

# 启动
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "在 macOS 上启动..."
    open "$APP_DIR/$APP_NAME"
else
    echo "在 Linux 上启动..."
    sudo "$APP_DIR/start.sh" &
    echo "启动命令已执行"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') 升级脚本完成"