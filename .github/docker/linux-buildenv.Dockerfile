ARG BASE_IMAGE=python:3.12-slim-buster
FROM ${BASE_IMAGE}

# 替换 apt 源为清华（两种架构通用）
#RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
#    sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
#    sed -i '/buster-updates/d' /etc/apt/sources.list

# 安装系统依赖
# 安装 C 编译器、Python 开发头文件、其他常用构建工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    gcc \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    wget \
    jq \
    zip \
    rsync \
    && rm -rf /var/lib/apt/lists/*

# armv7、riscv64 不支持
# 安装 Node.js 24 (自动适配架构)
#RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
#    apt-get install -y --no-install-recommends nodejs && \
#    rm -rf /var/lib/apt/lists/*

# 更新pip
RUN python3 -m pip install --upgrade pip setuptools wheel