#!/bin/bash

et_version() {
    local min_et_version='2.6.4'
    local fetch_url="https://api.github.com/repos/EasyTier/EasyTier/releases/latest"

    # 检查 jq 是否存在
    if ! command -v jq &> /dev/null; then
        echo "错误：需要安装 jq" >&2
        exit 1
    fi

    # 带超时和重试的 curl，保存错误输出
    local latest_release
    local curl_error
    latest_release=$(curl -fsSL --max-time 15 --retry 1 "${fetch_url}" 2>&1)
    curl_exit_code=$?

    if [ -z "$latest_release" ] || [ $curl_exit_code -ne 0 ]; then
        echo "错误：获取最新 EasyTier 版本信息失败" >&2
        echo "  URL: ${fetch_url}" >&2
        echo "  curl 退出码: ${curl_exit_code}" >&2
        if [ -n "$latest_release" ]; then
            echo "  错误信息: ${latest_release}" >&2
        else
            echo "  错误信息: 服务器无响应或返回空内容" >&2
        fi
        echo "  请检查网络连接或稍后重试" >&2
        ET_VER="$min_et_version"
#        exit 1
    fi

    # 提取版本号
    local et_version
    et_version=$(echo "$latest_release" | jq -r .tag_name | sed 's/^v//')

    if [ -z "${et_version}" ]; then
        echo "获取最新 EasyTier 版本号失败，版本信息：${latest_release}" >&2
        exit 1
    fi

    # 语义化版本比较（修正核心问题）
    version_ge() {
    # $1 >= $2 ?
    # 用 sort -V 排序后取第一行，如果第一行是 $2，说明 $2 <= $1
        [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | head -n1)" = "$2" ]
    }

    if ! version_ge "$et_version" "$min_et_version"; then
        echo "EasyTier release 版本 ${et_version} 过低，使用最低构建版本 ${min_et_version}" >&2
        et_version="$min_et_version"
    fi

    # 通过全局变量"返回"值
    ET_VER="$et_version"
}

app_info() {
  # 转换版本号
  local et_version=$ET_VER
  local et_version_raw
  if [ -f "./version-util.sh" ]; then
      chmod +x "version-util.sh"
      et_version_raw=$(./version-util.sh -x "$et_version")
  else
      echo "错误：version-util.sh 不存在" >&2
      exit 1
  fi

#  echo "转换 easytier 版本 ${et_version} 为 ${et_version_raw}" >&2
  ET_VER_RAW="$et_version_raw"

  CHANGE_LOG_FILE="CHANGELOG.md"
  CHANGE_VER=$(awk '/^## / {print $2; exit}' "${CHANGE_LOG_FILE}")
  if [[ -z "${CHANGE_VER}" ]]; then
    # 如果第一个出现的版本号为空，则取第二个版本号
    CHANGE_VER=$(awk '/^## / {c++; if(c==2) {print $2; exit}}' "${CHANGE_LOG_FILE}")
  fi

  prerelease='true'
  version="${CHANGE_VER}.${et_version_raw}"
  if git ls-remote --tags origin "refs/tags/$CHANGE_VER*" | grep -q .; then
    echo "存在 $CHANGE_VER 开头的 tag"
    # 指定东八区时间，确保GitHub action构建时间与本地时间一致
    version="${version}-$(TZ='Etc/GMT-8' date +'%Y%m%d%H%M%S')"
  else
    echo "不存在 $CHANGE_VER 开头的 tag"
    prerelease='false'
  fi

#    awk -v ver="$CHANGE_VER" '
#          $0 ~ "^## " ver { found=1; next }
#          found && $0 ~ "^## " { exit }
#          found { print }
#        ' "${CHANGE_LOG_FILE}" > release_notes.txt
  release_notes=$(awk '/^## /{if(p) exit; p=1; next} p' "${CHANGE_LOG_FILE}")

  BUILD_VER="${version}"
  CHANGE_NOTES="${release_notes}"
  PRE_RELEASE="${prerelease}"
#  rm -f release_notes.txt
}

# et 版本
ET_VER="$1"
# 构建版本
BUILD_VER="$2"
# 变更说明
CHANGE_NOTES="$3"
# 是否稳定版本
PRE_RELEASE="$4"

# 获取 et 版本号，转义版本号
et_version
app_info