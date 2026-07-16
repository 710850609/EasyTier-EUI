ARG BASE_IMAGE=alpine:3.20
FROM ${BASE_IMAGE}

# Alpine 3.20 自带 Python 3.12，无需从源码编译
RUN apk add --no-cache \
    build-base gcc binutils \
    openssl-dev zlib-dev bzip2-dev readline-dev \
    sqlite-dev ncurses-dev libffi-dev xz-dev \
    linux-headers \
    wget ca-certificates git curl jq zip rsync \
    python3 python3-dev py3-pip

ARG PYPI_MIRROR="https://pypi.org/simple"

RUN python3 -m pip install --break-system-packages --upgrade pip setuptools wheel -i ${PYPI_MIRROR} && \
    python3 -m pip install --break-system-packages pyinstaller psutil requests -i ${PYPI_MIRROR}

WORKDIR /app