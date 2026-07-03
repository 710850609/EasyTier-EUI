# EasyTier-EUI

![Downloads](https://img.shields.io/github/downloads/710850609/EasyTier-EUI/total?color=blue)
![Version](https://img.shields.io/github/v/release/710850609/EasyTier-EUI?color=blue)
![Version](https://img.shields.io/github/v/tag/710850609/EasyTier-EUI?color=blue)
![Stars](https://img.shields.io/github/stars/710850609/EasyTier-EUI?style=social)
![License](https://img.shields.io/github/license/710850609/EasyTier-EUI)

[//]: # ([![Ask DeepWiki]&#40;https://deepwiki.com/badge.svg&#41;]&#40;https://deepwiki.com/710850609/EasyTier-EUI&#41;)

## 目录

- [简介](#简介)
- [快速开始](#快速开始)
- [功能简介](#功能简介)
- [UI界面说明](#UI界面说明)
- [技术栈](#技术栈)
- [其他链接](#其他链接)
- [贡献](#贡献)
- [支持项目](#支持项目)
- [开源协议](#开源协议)

## 简介

<p>简化使用EasyTier的一种UI界面，快速组网（关闭后不影响组网运行）</p>
<p>更合适于无公网IPv4场景</p>
<p>飞牛版本基于CGI模式实现，不查看组网情况下，仅运行EasyTier核心服务，尽量减少内存使用</p>

## 快速开始

1. 前往 [Releases](https://github.com/710850609/EasyTier-EUI/releases) 页面，下载对应平台的安装包
2. 运行程序包 ```EasyTier-EUI```
3. 在「配置」页面添加组网配置，新手推荐快速模式配置，填入网络名和密钥即可
4. 其它设备加入虚拟网络：在「应用」菜单，根据设备系统架构选择对应安装包，根据页面说明，加入组网
5. 在「节点」页面查看组网状态，完成！


## 功能简介
- 支持多平台

| 平台           | 架构 | 备注                                                                             |
|--------------|------|--------------------------------------------------------------------------------|
| FnOS         | x86_64, aarch64 | root版本, 用户版本                                                                   |
| Windows      | x86_64 | Windows10及其以上版本                                                                |
| Linux | x86_64, aarch64, riscv64 | 已验证支持最低版本：Ubuntu 20.04 / Debian 10 / UOS 20；</br> 支持有图形界面（GUI）和无图形界面（Headless） |
| MacOS        | Intel, arm64 | 未验证                                                                            |
- 快速组网，仅填入网络名和密钥即可快速启动
- 提供其它设备组网应用（官方、其它常见第三方）下载连接、组网说明，快速组网
- 支持多配置
- 支持设置开机自启
- 支持EasyTier常见设置项
- 提供静态、动态初始节点（数据来自网络社区）
- 支持基于本地网络环境，进行初始节点检测：可用性、延迟、可中转
- UI自适应大、小屏幕，支持暗黑模式
- 内置 Github 加速下载，解决某些网络下载失败问题
- Linux版本启动时，会尝试打开本地浏览器访问页面。如果本地没用浏览器或是无图形界面，会在命令窗口中显示访问地址和二维码，可通过同个局域网其它设备访问（比如手机扫码访问）。


## UI界面说明
### 节点
- 查看各个节点的组网状态
- 支持按需设置显示列信息、显示普通节点、服务节点
- 支持设置数据刷新速度

### 配置
- 支持快速组网，仅填入网络名和密码即可快速启动，合适新手、懒人使用
- 支持界面可视化配置```EasyTier```常见配置项。对于冷门配置，可通过界面编辑文件的形式进行手动编辑配置内容
- 支持多个配置
- 支持设置开机自启
- 支持分享网络，将当前配置分享给其它设备
- 支持服务节点检测，包括：可用性、延迟、可中转

### 应用
- 支持```EasyTier```其它平台、架构的组网应用下载，包括：Windows、Linux、MacOS、FnOS、Android、IOS、HarmonyOS，方便下载安装，为快速组网作准备。
- ```易组网```, ```easytier-manager-pro```2种应用下载时，会内置当前设备组网配置，以方便快速组网

### 设置
- 支持设置界面主题，包括：暗黑模式、亮色模式
- 支持```EasyTier```查看各个版本的更新内容、GitHub下载量、安装指定内核版本。无须访问GitHub，即可查看最新和历史版本信息。
- 支持```易组网```稳定版、预发版查看更新内容、自更新



## 界面

### 大屏界面

| 节点管理 | 配置管理 |
|----------|----------|
| ![节点管理](assets/nodes-pc1.png) | ![配置管理](assets/config-pc3.png) |
| ![节点管理](assets/nodes-pc2.png) | ![配置管理](assets/config-pc1.png) |

| 配置管理 | 应用下载 |
|----------|----------|
| ![配置管理](assets/config-pc2.png) | ![应用下载](assets/download-pc1.png) |

| 设置 |
|------|
| ![设置](assets/setting-pc1.png) |

### 小屏界面

| 节点管理 | 配置管理 | 配置管理 |
|----------|----------|----------|
| ![节点管理](assets/nodes-m1.png) | ![配置管理](assets/config-m2.png) | ![配置管理](assets/config-m1.png) |

| 应用下载                            | 设置 |
|---------------------------------|------|
| ![应用下载](assets/download-m1.png) | ![设置](assets/setting-m1.png) |

## 技术栈

| 层级   | 技术                                                                   |
|------|----------------------------------------------------------------------|
| 桌面框架 | [pywebview](https://pywebview.flowrl.com/)                                          |
| 前端   | [Vue 3](https://vuejs.org/) + [Varlet UI](https://www.varletjs.com/) |
| 后端   | [Python3](https://www.python.org/)                                       |
| 组网内核 | [EasyTier](https://github.com/EasyTier/EasyTier)                     |

## 其他链接

- <a href="https://github.com/EasyTier/EasyTier" target="_blank" rel="noopener noreferrer">EasyTier 源码</a>
- <a href="https://easytier.cn" target="_blank" rel="noopener noreferrer">EasyTier 文档</a>
- <a href="https://www.varletjs.com/#/zh-CN" target="_blank" rel="noopener noreferrer">Varlet 文档</a>

## 贡献

欢迎提交 Issue 和 Pull Request！

- 🐛 [提交 Bug 反馈](https://github.com/710850609/EasyTier-EUI/issues/new?template=bug_report.yml)
- ✨ [提出功能建议](https://github.com/710850609/EasyTier-EUI/issues/new?template=feature_request.yml)

## 支持项目

如果这个项目对你有帮助，欢迎 **Star ⭐** 或是 赞赏 支持！

<p align="center">
  <img src="frontend/public/images/reward_code.jpg" width="200" />
</p>

## 开源协议

本项目基于 [GPL-3.0 License](LICENSE) 开源。