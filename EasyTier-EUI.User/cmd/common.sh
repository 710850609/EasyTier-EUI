#!/bin/bash

### This script is called after the user installs the application.
set -e

LOG_FILE="${TRIM_PKGVAR}/logs/cmd.log"
BIN_DIR="${TRIM_APPDEST}/bin"
CFG_FILE="${TRIM_APPDEST_VOL}/@appshare/${TRIM_APPNAME}/config.toml"
INIT_FILE="${TRIM_PKGVAR}/.init"
GITHUB_PROXY_URL_CFG_FILE="${TRIM_APPDEST}/github_proxy_url.txt"
SCRIPT_PATH="${TRIM_APPDEST}/backend"


log_msg() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> ${LOG_FILE}
}

warm_exit() {
    log_msg "$1"
    echo "$1" > ${TRIM_TEMP_LOGFILE}
    exit 1
}

run_cmd() {
    log_msg "运行命令: $1"
    bash -c "$1" >> ${LOG_FILE} 2>&1
}

makesure_cfg_file() {
    log_msg "检查配置文件: ${CFG_FILE}"
    if [ ! -f ${CFG_FILE} ]; then
        run_cmd "mkdir -p $(dirname ${CFG_FILE})"
        run_cmd "cp -f ${TRIM_APPDEST}/default.toml ${CFG_FILE}"
        log_msg "不存在配置文件，使用默认配置: ${CFG_FILE}"
        run_cmd "touch ${INIT_FILE}"
        # 安装新场景，生成随机网络名称、网络密码
        if [ "${TRIM_APP_STATUS}" == "INSTALL" ]; then
            log_msg "安装应用，生成随机网络名称、网络密码"
            nw_name=$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 8 | head -n 1)
            nw_password=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
            update_network ${nw_name} ${nw_password}
        fi
    fi
}

save_github_porxy_url() {
    run_cmd "echo ${github_proxy_url} > ${GITHUB_PROXY_URL_CFG_FILE}"
}

update_network() {
    local network_name=${1:-${et_network_name}}
    local network_secret=${2:-${et_network_secret}}
    log_msg "更新网络: ${network_name}"
    run_cmd "sed -i 's/^network_name.*/network_name = \"${network_name}\"/' ${CFG_FILE}"
    run_cmd "sed -i 's/^network_secret.*/network_secret = \"${network_secret}\"/' ${CFG_FILE}"
}

change_et_version() {
    local new_et_version=${1:-${et_version}}
    local github_proxy_url=${2:-${github_proxy_url}}
    local version_output=$("${bin_dir}/easytier-core" --version 2>&1)
    local cur_et_version=$(echo "$version_output" | grep -oP 'easytier-core \K(\d+\.\d+\.\d+)')
    if [ "$new_et_version" == "$cur_et_version" ]; then
        log_msg "当前 easytier 版本已经是 $cur_et_version, 无需修改EasyTier核心版本"
        return 0
    fi

    local arch=$(uname -m)
    local download_url="https://github.com/EasyTier/EasyTier/releases/download/v${new_et_version}/easytier-linux-${arch}-v${new_et_version}.zip"
    if [ "$github_proxy_url" != "" ]; then
        download_url=${github_proxy_url}/${download_url}
    fi
    local temp_dir="${TRIM_PKGTMP}/core-change"
    run_cmd "mkdir -p ${temp_dir}"
    local download_file="${temp_dir}/easytier-linux-${arch}-${new_et_version}.zip"
    run_cmd "rm -f ${download_file}"
    log_msg "开始下载: ${download_url} , 保存到 ${download_file}"
    run_cmd "wget -O ${download_file} ${download_url}"
    if [ ! -f "${download_file}" ]; then
        warm_exit "下载 EasyTier 失败"
    fi
    log_msg "下载 EasyTier 成功: ${download_file}, 开始解压"
    run_cmd "unzip -o ${download_file} -d ${temp_dir}"
    run_cmd "cp -rf ${temp_dir}/easytier-linux-${arch}/easytier-cli ${BIN_DIR}"
    run_cmd "cp -rf ${temp_dir}/easytier-linux-${arch}/easytier-core ${BIN_DIR}"
    run_cmd "rm -rf ${temp_dir}"
    log_msg "成功修改EasyTier核心版本为: ${new_et_version}"
}

download_win() {
    if [ "$enable_win_package" != "true" ]; then
        log_msg "未开启生成Windows版本，无需下载"
        return 0
    fi
    local output_file="/var/apps/${TRIM_APPNAME}/shares/${TRIM_APPNAME}/easytier-manager-pro_${cur_et_version}.zip"
    if [ -f "${output_file}" ]; then
        log_msg "Windows EasyTier 版本 ${cur_et_version} 已存在，无需下载"
        return 0
    fi
    local version_output=$("${BIN_DIR}/easytier-core" --version 2>&1)
    local cur_et_version=$(echo "$version_output" | grep -oP 'easytier-core \K(\d+\.\d+\.\d+)')
    local temp_dir="${TRIM_PKGTMP}/easytier-windows-x86_64"
    run_cmd "rm -rf ${temp_dir}"
    run_cmd "mkdir -p ${temp_dir}"

    local download_url="https://github.com/EasyTier/EasyTier/releases/download/v${cur_et_version}/easytier-windows-x86_64-v${cur_et_version}.zip"
    if [ "$github_proxy_url" != "" ]; then
        download_url=${github_proxy_url}/${download_url}
    fi
    local download_file="${temp_dir}/easytier-windows-x86_64-${cur_et_version}.zip"
    run_cmd "rm -f ${download_file}"
    log_msg "开始下载: ${download_url} , 保存到 ${download_file}"
    run_cmd "wget -O ${download_file} ${download_url}"
    if [ ! -f "${download_file}" ]; then
        warm_exit "下载 Windows EasyTier 失败"
    fi
    log_msg "下载 EasyTier 成功: ${download_file}, 开始解压"
    run_cmd "unzip -o ${download_file} -d ${temp_dir}"
    run_cmd "rm -f ${download_file}"

    log_msg "下载最新 EasyTier Manager Pro"
    download_url="https://github.com/EasyTier/easytier-manager/releases/latest/download/easytier-manager-pro.zip"
    if [ "$github_proxy_url" != "" ]; then
        download_url=${github_proxy_url}/${download_url}
    fi 
    download_file="${temp_dir}/easytier-manager-pro.zip"
    run_cmd "rm -f ${download_file}"
    log_msg "开始下载: ${download_url} , 保存到 ${download_file}"
    run_cmd "wget -O ${download_file} ${download_url}"
    if [ ! -f "${download_file}" ]; then
        warm_exit "下载 easytier-manager-pro 失败"
    fi
    log_msg "下载 easytier-manager-pro 成功: ${download_file}, 开始解压"
    run_cmd "unzip -o ${download_file} -d ${temp_dir}/easytier-manager-pro | grep -v "warning:" || true"
    run_cmd "rm -rf ${download_file}"
    
    log_msg "开始打包..."
    # 复制et核心
    run_cmd "cp -rf ${temp_dir}/easytier-windows-x86_64/* ${temp_dir}/easytier-manager-pro/resource/"
    # 复制配置文件，并修改成DHCP分配ip
    run_cmd "mkdir -p ${temp_dir}/easytier-manager-pro/config"
    run_cmd "cp -rf ${CFG_FILE} ${temp_dir}/easytier-manager-pro/config/et-fnos.toml"
    run_cmd "sed -i 's/^dhcp.*/dhcp = \"true\"/' ${temp_dir}/easytier-manager-pro/config/et-fnos.toml"
    run_cmd "sed -i 's/^ipv4.*/ipv4 = \"\"/' ${temp_dir}/easytier-manager-pro/config/et-fnos.toml"

    run_cmd "cd ${temp_dir} && zip -r ${output_file} ./easytier-manager-pro/"
    log_msg "打包 easytier-manager-pro 成功: ${output_file}"
    run_cmd "rm -rf ${temp_dir}"
}