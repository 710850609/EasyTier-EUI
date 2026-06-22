#!/bin/bash

DOWNLOAD_FILE="unknown"

declare -A PARAMS
# 默认值
PARAMS[build_all]="false"
PARAMS[download_proxy]="true"
PARAMS[proxy_url]="https://ghfast.top"
PARAMS[arch]="x86_64"
PARAMS[app_name]="EasyTier-EUI"
# 解析 key=value 格式的参数
for arg in "$@"; do
  if [[ "$arg" == *=* ]]; then
    key="${arg%%=*}"
    value="${arg#*=}"
    PARAMS["$key"]="$value"
  else
    # 处理标志参数
    case "$arg" in
      --pre)
        PARAMS[pre]="true"
        ;;
      *)
        echo "忽略未知参数: $arg"
        ;;
    esac
  fi
done

if [[ "${PARAMS[app_name]}" != "EasyTier-EUI" && "${PARAMS[app_name]}" != "EasyTier-EUI.User" ]]; then
  echo "错误：app_name 参数必须为 EasyTier-EUI 或 EasyTier-EUI.User"
  exit 1
fi

build_all="${PARAMS[build_all]}"
download_proxy="${PARAMS[download_proxy]}"
proxy_url="${PARAMS[proxy_url]}"
arch="${PARAMS[arch]}"
app_name="${PARAMS[app_name]}"
bin_dir="${app_name}/app/bin"
echo "build_all: ${build_all}"
echo "download_proxy: ${download_proxy}"
echo "proxy_url: ${proxy_url}"
echo "arch: ${arch}"
echo "app_name: ${app_name}"
echo "bin_dir: ${bin_dir}"


# platform 取值 x86, arm, risc-v, all
platform=""
et_platform=""
os_min_version="1.0.0"
if [ "${arch}" == "x86_64" ]; then
    platform="x86"
    et_platform="x86_64"
    os_min_version="1.1.8"
    py_platform="manylinux_2_28_x86_64"
elif [ "${arch}" == "aarch64" ]; then
    platform="arm"
    et_platform="aarch64"
    os_min_version="1.0.2"
    py_platform="manylinux_2_28_aarch64"
elif [ "${arch}" == "linux-riscv64" ]; then
    platform="riscv64"
    py_platform="manylinux_2_34_riscv64"
    os_min_version="1.0.0"
else
    echo "不支持的 arch 参数"
    exit 1
fi
echo "设置 platform 为: ${platform}"
echo "---------------------------------------"

ensure_build_info() {
  # et 版本
  ET_VER="${PARAMS[et_ver]}"
  # 构建版本
  BUILD_VER="${PARAMS[build_ver]}"
  # 变更说明
  CHANGE_NOTES="${PARAMS[change_notes]}"
  if [[ -z "${ET_VER}" || -z "${BUILD_VER}" ]]; then
      echo "没同时传入 et_ver, build_ver 立即获取构建信息"
     if [ -f "./build-info.sh" ]; then
        chmod +x "build-info.sh"
        source build-info.sh "${ET_VER}" "${BUILD_VER}" "${CHANGE_NOTES}" ""
    else
        echo "错误：build-info.sh 不存在" >&2
        exit 1
    fi
  fi

  echo "ET_VER = ${ET_VER}"
  echo "BUILD_VER = ${BUILD_VER}"
  echo "CHANGE_NOTES = ${CHANGE_NOTES}"
}

build_backend() {
    # 写入构建版本号
    target_file='backend/utils/run_configs.py'
    echo "  写入构建版本号: ${BUILD_VER}"
    awk -v ver="$BUILD_VER" '
      /^BUILD_VERSION = "/ { print "BUILD_VERSION = \"" ver "\""; next }
      { print }
    ' "$target_file" > "${target_file}.tmp" && mv "${target_file}.tmp" "$target_file"

    echo "下载py依赖"
    rm -rf "${app_name}/app/backend"
    mkdir -p "${app_name}/app/backend/wheels"
    # 下载 wheel
    app_script_path="${app_name}/app/backend"
    pip download \
        --only-binary=:all: \
        --platform $py_platform \
        --python-version 311 \
        -r backend/requirements-base.txt \
        -d ${app_script_path}/wheels
        
    echo "写入脚本到app"
    rsync -a --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='build' \
    --exclude='dist' \
    --exclude='assets' \
    --exclude='build.py' \
    --exclude='build_core.py' \
    --exclude='http_dispatcher/http_server.py'  \
    --exclude='main_noui.py'  \
    --exclude='main_ui.py'  \
    --exclude='requirements-gui.txt'  \
    --exclude='shell' \
    --exclude='*.sh' \
    backend/ "${app_script_path}/"
}

build_frontend() {
    if [ "${build_all}" == "true" ] || [ ! -f "frontend/dist/index.html" ]; then
      echo '编译前端...'
      if ! command -v node &> /dev/null; then
          echo "当前环境未找到 node 命令，设置 node 环境..."
          node_ver=24
          export PATH="/var/apps/nodejs_v$node_ver/target/bin:$PATH"
          if ! command -v node &> /dev/null; then
              echo "nodejs ${node_ver} 不存在"
              exit 1
          fi
          echo "已设置 node ${node_ver} 环境"
      fi
      echo "使用node版本: $(node -v)"
      cd frontend
      npm install
      npm run build
      cd ../
    else
      echo "已存在前端编译资源，跳过编译前端"
    fi
    rm -rf "${app_name}/app/frontend"
    mkdir -p "${app_name}/app/frontend"
    cp -rf frontend/dist/* "${app_name}/app/frontend"
    echo "拷贝前端资源到 ${app_name}/app/frontend 目录"
}

download_et() {
    DOWNLOAD_FILE="easytier-linux-${et_platform}-${ET_VER}.zip"
    # 非当前系统，强制下载最新版本，避免后续版本判断错误
    if [ "${build_all}" == "true" ] || [ ! -f "${DOWNLOAD_FILE}" ]; then
        local download_url="https://github.com/EasyTier/EasyTier/releases/download/v${ET_VER}/easytier-linux-${et_platform}-v${ET_VER}.zip"
        if [ "$download_proxy" == "true" ]; then
            download_url=${proxy_url}/${download_url}
        fi
        rm -f "${DOWNLOAD_FILE}"
        echo "开始下载: ${download_url}"
        wget -O "${DOWNLOAD_FILE}" "${download_url}"
        if [ ! -f "${DOWNLOAD_FILE}" ]; then
            echo "下载 EasyTier 失败"
            exit 1
        fi
    fi
}

update_app() {
    local temp_dir="temp"
    bash -c "rm -rf ${bin_dir}" 2>&1
    bash -c "mkdir -p ${bin_dir}" 2>&1
    bash -c "mkdir -p ${temp_dir}" 2>&1
    echo "开始解压 ${DOWNLOAD_FILE}"
    bash -c "unzip -o ${DOWNLOAD_FILE} -d ${temp_dir}" 2>&1
    echo "开始复制应用文件"
    bash -c "cp -rf ${temp_dir}/easytier-linux-${et_platform}/easytier-cli ${bin_dir}" 2>&1
    bash -c "cp -rf ${temp_dir}/easytier-linux-${et_platform}/easytier-core ${bin_dir}" 2>&1
    # User 版本：修改默认 APPNAME
    if [ "${app_name}" == "EasyTier-EUI.User" ]; then
        sed -i "s|DEFAULT_TRIM_APPNAME:str = 'EasyTier-EUI'|DEFAULT_TRIM_APPNAME:str = 'EasyTier-EUI.User'|" "${app_name}/app/backend/utils/run_configs.py"
        echo "已修改 DEFAULT_TRIM_APPNAME 为 EasyTier-EUI.User"
    fi
    echo "更新应用文件完成"
    echo "---------------------------------------"
}


build_fpk() {
    local fpk_version=$BUILD_VER
    sed -i "s|^[[:space:]]*version[[:space:]]*=.*|version=${fpk_version}|" "${app_name}/manifest"
    echo "设置 manifest 的 version 为: ${fpk_version}"
    sed -i "s|^[[:space:]]*platform[[:space:]]*=.*|platform=${platform}|" "${app_name}/manifest"
    echo "设置 manifest 的 platform 为: ${platform}"
    sed -i "s|^[[:space:]]*os_min_version[[:space:]]*=.*|os_min_version=${os_min_version}|" "${app_name}/manifest"
    echo "设置 manifest 的 os_min_version 为: ${os_min_version}"

    echo "开始打包 fpk"
    if command -v fnpack >/dev/null 2>&1; then
        echo "使用系统已安装的 fnpack 进行打包"
        fnpack build --directory "${app_name}/"  || { echo "打包失败"; exit 1; }
    else
        echo "使用本地 fnpack 脚本进行打包"
        ./fnpack.sh build --directory "${app_name}" || { echo "打包失败"; exit 1; }
    fi 

    fpk_name="${app_name}-fnos-${arch}-${fpk_version}.fpk"
    rm -f "${fpk_name}"
    mv "${app_name}.fpk" "${fpk_name}"
    echo "打包完成: ${fpk_name}"
}

ensure_build_info
build_backend
build_frontend
download_et
update_app


build_fpk

exit 0