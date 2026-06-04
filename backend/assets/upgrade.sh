#!/bin/bash

# 用法检查
if [ -z "$1" ]; then
    echo "用法: $0 \"安装路径\""
    exit 1
fi

APP_DIR="$1"
UPDATE_DIR="$APP_DIR/_update"
APP_NAME="EasyTier-EUI"

# 等待进程结束
while pgrep -x "$APP_NAME" > /dev/null 2>&1; do
    killall -9 "$APP_NAME" > /dev/null 2>&1
    sleep 1
done

# 替换文件
mv -f "$UPDATE_DIR/$APP_NAME" "$APP_DIR/$APP_NAME"
mv -f "$UPDATE_DIR/_internal" "$APP_DIR/_internal"

# 清理更新目录
rm -rf "$UPDATE_DIR"

# 启动
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$APP_DIR/$APP_NAME"
else
    # Linux
    chmod +x "$APP_DIR/$APP_NAME"
    "sudo $APP_DIR/start.sh" &
fi