# ============================================
# EasyTier-EUI 运行时 Docker 镜像
# 基于 Alpine musl，与 build-linux-alpine 构建产物一致
# 无需 glibc 兼容层，镜像体积最小
# ============================================

FROM alpine:3.20

LABEL org.opencontainers.image.source="https://github.com/710850609/EasyTier-EUI"
LABEL org.opencontainers.image.description="EasyTier-EUI - Web-based GUI for EasyTier"

RUN apk add --no-cache ca-certificates curl

WORKDIR /app

COPY EasyTier-EUI /app/EasyTier-EUI
COPY core/ /app/core/
COPY start.sh /app/start.sh
COPY stop.sh /app/stop.sh

RUN chmod +x /app/EasyTier-EUI /app/core/easytier-core /app/core/easytier-cli /app/start.sh /app/stop.sh

RUN mkdir -p /app/data /app/logs /app/config

VOLUME ["/app/config"]

ENV PORT=5666

EXPOSE ${PORT}

ENTRYPOINT ["sh", "-c", "/app/EasyTier-EUI --port ${PORT}"]