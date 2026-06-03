#!/bin/bash

APP_NAME="EasyTier-EUI"
# 卸载应用
echo "卸载应用..."
sudo appcenter-cli uninstall ${APP_NAME}

# 找到最新的 fpk 文件
LATEST_FPK=$(ls *.fpk 2>/dev/null | sort -V | tail -n 1)

if [ -z "$LATEST_FPK" ]; then
    echo "错误：未找到 .fpk 文件"
    exit 1
fi

echo "安装包: $LATEST_FPK"

# 安装 fpk
sudo appcenter-cli install-fpk "$LATEST_FPK" --env config.env

# 启动应用
echo "启动应用..."
sudo appcenter-cli start ${APP_NAME}

echo "安装完成！"
