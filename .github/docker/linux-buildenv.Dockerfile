ARG BASE_IMAGE=debian:buster
FROM ${BASE_IMAGE}

# 换归档源（buster 已 EOL，必须用 archive.debian.org）
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list && \
    sed -i '/buster-updates/d' /etc/apt/sources.list && \
    apt-get update -o Acquire::Check-Valid-Until=false && \
    apt-get install -y --no-install-recommends \
        build-essential gcc binutils libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev libncurses5-dev \
        libncursesw5-dev libffi-dev liblzma-dev tk-dev uuid-dev \
        wget ca-certificates git curl jq zip rsync \
    && rm -rf /var/lib/apt/lists/*

# 编译参数（放在 FROM 之后，确保可用）
ARG PYTHON_VERSION=3.12.4
ARG PYPI_MIRROR="https://pypi.org/simple"

# 下载并编译 Python 3.12
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

# 创建 python3 / pip3 软链接，解决命令不识别问题
RUN ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3 && \
    ln -sf /usr/local/bin/python3.12 /usr/local/bin/python && \
    ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip3 && \
    ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip

# 升级 pip 并安装打包工具
RUN python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade pip setuptools wheel -i ${PYPI_MIRROR} && \
    python3 -m pip install pyinstaller psutil requests -i ${PYPI_MIRROR}

WORKDIR /app