ARG BASE_IMAGE=debian:buster
FROM ${BASE_IMAGE}

# 换国内源（可选，取消注释即可）
# RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
#     sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 一步安装所有系统依赖（编译 Python + 后续 C 扩展所需）
# 换归档源（buster 已 EOL，必须用 archive.debian.org）
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list && \
    sed -i '/buster-updates/d' /etc/apt/sources.list && \
    apt-get update -o Acquire::Check-Valid-Until=false && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        binutils \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libncurses5-dev \
        libncursesw5-dev \
        libffi-dev \
        liblzma-dev \
        tk-dev \
        uuid-dev \
        wget \
        ca-certificates \
        git \
        curl \
        jq \
        zip \
        rsync \
    && rm -rf /var/lib/apt/lists/*

# 下载并编译 Python 3.12
# 编译参数
ARG PYTHON_VERSION=3.12.4
ARG PYPI_MIRROR="https://pypi.org/simple"
# 注意：在 ARM QEMU 模拟环境下编译较慢，如需加速可去掉 --enable-optimizations
RUN wget -q https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar xzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure \
        --prefix=/usr/local \
        --enable-shared \
        --with-ensurepip=install \
        LDFLAGS="-Wl,-rpath,/usr/local/lib" && \
    make -j$(nproc) && \
    make altinstall && \
    cd .. && \
    rm -rf Python-${PYTHON_VERSION}* && \
    ldconfig

# 升级 pip 并安装打包工具
RUN /usr/local/bin/python3.12 -m ensurepip --upgrade && \
    /usr/local/bin/python3.12 -m pip install --upgrade pip setuptools wheel -i ${PYPI_MIRROR} && \
    /usr/local/bin/pip3.12 install pyinstaller psutil requests -i ${PYPI_MIRROR}

WORKDIR /app