# ============================================
# EasyTier-EUI 运行时 Docker 镜像
# 基于 PyInstaller 打包好的 Linux 二进制
# 基础镜像选 Debian Bookworm Slim：glibc 2.36，兼容构建环境(glibc 2.28)，体积小
# 不可用 Alpine：PyInstaller 二进制依赖 glibc，非 musl
# ============================================

FROM debian:bookworm-slim

LABEL org.opencontainers.image.source="https://github.com/710850609/EasyTier-EUI"
LABEL org.opencontainers.image.description="EasyTier-EUI - Web-based GUI for EasyTier"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY EasyTier-EUI /app/EasyTier-EUI
COPY core/ /app/core/
COPY start.sh /app/start.sh
COPY stop.sh /app/stop.sh

RUN chmod +x /app/EasyTier-EUI /app/core/easytier-core /app/core/easytier-cli /app/start.sh /app/stop.sh

RUN mkdir -p /app/data /app/logs /app/config

VOLUME ["/app/data", "/app/logs", "/app/config", "/app/core"]

ENV PORT=5666

EXPOSE ${PORT}

ENTRYPOINT ["sh", "-c", "/app/EasyTier-EUI --port ${PORT}"]