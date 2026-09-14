#!/bin/sh
# EasyTier-EUI dynv6 DNS TXT 记录更新脚本
# 用法: ./update_dns_dynv6.sh <protocol> <publicIp> <publicPort> <zoneName> <subdomain> [apiToken]
# 示例: ./update_dns_dynv6.sh "tcp" "1.2.3.4" "8080" "example.com" "_acme-challenge" "your-api-token"
# 支持最多 3 次重试

set -e

DYNV6_API="https://dynv6.com/api/v2"
SCRIPT_NAME="update_dns_dynv6.sh"
MAX_RETRY=3
RETRY_DELAY=2

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$SCRIPT_NAME] $*"
}

retry() {
    local label="$1"
    shift
    local i=1
    local retry_err
    while [ $i -le $MAX_RETRY ]; do
        retry_err=$(mktemp)
        if "$@" 2>"$retry_err"; then
            rm -f "$retry_err"
            return 0
        fi
        local curl_rc=$?
        local err_msg=$(cat "$retry_err" 2>/dev/null)
        rm -f "$retry_err"
        log "${label} 第${i}次失败, curl exit=${curl_rc}, error=${err_msg}"
        if [ $i -lt $MAX_RETRY ]; then
            log "${label} ${RETRY_DELAY}秒后重试..."
            sleep $RETRY_DELAY
        fi
        i=$((i + 1))
    done
    log "错误: ${label} 已重试${MAX_RETRY}次，全部失败"
    return 1
}

if [ $# -lt 4 ]; then
    log "用法: $0 <protocol> <publicIp> <publicPort> <zoneName> <subdomain> [apiToken]"
    log "示例: $0 \"tcp\" \"1.2.3.4\" \"8080\" \"example.com\" \"_acme-challenge\""
    exit 1
fi

PROTOCOL="$1"
PUBLIC_IP="$2"
PUBLIC_PORT="$3"
ZONE_NAME="$4"
SUBDOMAIN="$5"
TOKEN="${6:-${DYNV6_API_TOKEN}}"

TXT_VALUE="${PROTOCOL}://${PUBLIC_IP}:${PUBLIC_PORT}"

if [ -z "$TOKEN" ]; then
    log "错误: 未设置 apiToken 参数或环境变量 DYNV6_API_TOKEN"
    exit 1
fi

FULL_RECORD_NAME="${SUBDOMAIN}.${ZONE_NAME}"

http_get() {
    curl -sfL \
        -H "Authorization: Bearer ${TOKEN}" \
        "$@"
}

http_patch() {
    curl -sfL -X PATCH \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        "$@"
}

http_post() {
    curl -sfL -X POST \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        "$@"
}

log "开始更新 DNS TXT 记录"
log "  域名: ${ZONE_NAME}"
log "  子域名: ${SUBDOMAIN}"
log "  完整记录名: ${FULL_RECORD_NAME}"
log "  记录值: ${TXT_VALUE}"

# Step 1: 根据域名查询 zoneId
log "查询 Zone ID..."
ZONES_JSON=$(retry "查询Zone" http_get "${DYNV6_API}/zones") || exit 1
log "  Zone API 返回: ${ZONES_JSON}"
ZONE_ID=$(echo "$ZONES_JSON" | sed 's/},{/}\n{/g' | grep '"name":"'"${ZONE_NAME}"'"' | sed 's/.*"id":\([0-9]*\).*/\1/')

if [ -z "$ZONE_ID" ]; then
    log "错误: 未找到域名 ${ZONE_NAME} 对应的 Zone"
    exit 1
fi
log "  Zone ID: ${ZONE_ID}"

# Step 2: 查询已有同名 TXT 记录，有则更新，无则新增
log "查询已有 TXT 记录..."
RECORDS_JSON=$(retry "查询记录" http_get "${DYNV6_API}/zones/${ZONE_ID}/records") || exit 1
log "  Records API 返回: ${RECORDS_JSON}"
RECORD_IDS=$(echo "$RECORDS_JSON" | sed 's/},{/}\n{/g' | grep '"name":"'"${SUBDOMAIN}"'"' | grep '"type":"TXT"' | sed 's/.*"id":\([0-9]*\).*/\1/')

if [ -n "$RECORD_IDS" ]; then
    for RECORD_ID in $RECORD_IDS; do
        log "更新已有 TXT 记录: ID=${RECORD_ID}"
        UPDATE_BODY=$(printf '{"data":"%s"}' "${TXT_VALUE}")
        log "  更新请求体: ${UPDATE_BODY}"
        UPDATE_RESULT=$(retry "更新记录" http_patch -d "$UPDATE_BODY" "${DYNV6_API}/zones/${ZONE_ID}/records/${RECORD_ID}") || exit 1
        log "  更新成功: ${UPDATE_RESULT}"
    done
else
    log "  未找到同名 TXT 记录，新增记录..."
    ADD_BODY=$(printf '{"name":"%s","type":"TXT","data":"%s"}' "${SUBDOMAIN}" "${TXT_VALUE}")
    log "  新增请求体: ${ADD_BODY}"
    ADD_RESULT=$(retry "新增记录" http_post -d "$ADD_BODY" "${DYNV6_API}/zones/${ZONE_ID}/records") || exit 1
    log "  新增成功: ${ADD_RESULT}"
fi

log "完成"