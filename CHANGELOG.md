##  2.1
- 新增：安卓版支持应用启动重连，自动运行上次未手动关闭的配置 ([Feature #9](https://github.com/710850609/EasyTier-EUI/issues/9))
- 优化：安卓版VPN支持IPv6、支持魔法DNS、支持MTU、根据物理网络自适应是否计量网络
- 优化：安卓版VPN排除干扰电话服务、常见推送服务、系统服务。手动强制路由时，尽量保证系统正常运行
- 修复：安卓版未能显示多个连接协议
----
- 优化：【设置】页面响应，各个页面亮模式视觉优化、安全区域适配、底部菜单栏毛玻璃效果
----
- 废弃：【应用】-IOS TestFlight 废弃
- 新增：【应用】-IOS 支持跳转App Store正式版下载
- 优化：小屏幕底部菜单、二级菜单及其页面显示
- 修复：【节点】页面底部安全区域适配
- 修复：ffi模式下，【节点】页面没显示ipv6相关协议，如：tcp6，udp6
- 
<br>

----

- New: Android version now supports app startup reconnect, automatically running the last config that was not manually stopped ([Feature #9](https://github.com/710850609/EasyTier-EUI/issues/9))
- Improved: Android VPN now supports IPv6, Magic DNS, MTU, and adaptive metered network detection based on physical network
- Improved: Android VPN excludes interference with phone services, common push services, and system services. When manually forcing routes, system operations are preserved as much as possible
- Fixed: Android version failed to display multiple connection protocols
----
- Optimized: [Settings] page responsiveness, light mode visual refinements across all pages, safe area adaptation, bottom navigation bar frosted glass effect
----
- Deprecated: [App] - iOS TestFlight deprecated
- New: [App] - iOS supports redirecting to App Store for official release download
- Improved: Small screen bottom menu, sub-menu and page display
- Fixed: [Nodes] page bottom safe area adaptation
- Fixed: Under FFI mode, [Nodes] page did not display IPv6-related protocols, such as tcp6, udp6

##  2.2
- 新增：【配置】支持二维码分享网络、支持扫描二维码增加配置
  - 仅支持https方式访问才能扫码（浏览器安全限制）
- 优化：【配置】只提交最小有效配置
- 优化：【节点】安卓版显示当前设备名
- 优化：安卓通知自适应中/英文显示，增加显示vpn uptime
- 修复：安卓后台被杀，小概率无法直接进入app
----
- 新增：【配置】支持从剪贴板添加配置
- 新增：【设置】增加GitHub反馈入口
- 新增：【应用】-Android 支持x86_64和x86架构
- 优化：【配置】扫码新增时，支持不填写配置名称，识别成功后立即保存
- 修复：【配置】保存配置时，界面设置没覆盖到配置已有配置项
- 修复：飞牛版本、Linux版本（非开机自启模式）、MacOS版本（非开机自启模式）、Docker版本下，关闭组网后，组网进程未被完全终止 ([issues #5](https://github.com/710850609/EasyTier-EUI/issues/5))
----
- 新增：安卓版本支持选择EasyTier内核版本
---- 
- 新增：安卓版本增加开屏动画，优化视觉体验
- 新增：【设置】-其它支持自定义可选初始节点
- 修复：飞牛版本在2.0时引入，某些情况下导致系统重启报错 ([issues #6](https://github.com/710850609/EasyTier-EUI/issues/6))
----
- 优化：【设置】合并请求，减少网络请求次数，按需请求必要数据返回，减少流量消耗
- 优化：安卓版本第一次申请摄像头权限后，页面被重置，操作中断不友好
- 优化：整体UI视觉，更圆润、更轻盈
- 优化：飞牛版本启动端口占用时，抛出 EasyTier 报错提示
- 修复：自定义初始节点默认易组网维护节点时，没显示在配置可选列表中

<br>

----

- Added: [Config] Support QR code sharing for network config, support scanning QR code to add config
  - QR scanning requires HTTPS access (browser security restriction)
- Improved: [Config] Only submit minimal valid configuration
- Improved: [Peers] Display current device name on Android
- Improved: Android notification adapts to Chinese/English display, added VPN uptime display
- Fixed: Rare issue where Android app couldn't be opened directly after being killed in background
----
- Added: [Config] Support adding configuration from clipboard
- Added: [Settings] Add GitHub feedback entry
- Added: [App] Android now supports x86_64 and x86 architectures
- Improved: [Config] QR scan add now supports saving without entering a config name, saves immediately after recognition
- Fixed: [Config] UI settings were not overriding existing config items when saving configuration
- Fixed: On FNOS, Linux (non-autostart mode), and macOS (non-autostart mode) and Docker, the networking process was not fully terminated after stopping the network (https://github.com/710850609/EasyTier-EUI/issues/5)
----
- Added: Android version supports selecting EasyTier kernel version
---- 
- Added: Splash screen animation on Android for improved visual experience
- Added: [Settings] - Support for custom optional initial nodes
- Fixed: FnOS version 2.0 caused system reboot error in certain cases ([issues #6](https://github.com/710850609/EasyTier-EUI/issues/6))
----
- Optimized: Merged requests in Settings to reduce network requests, fetch only necessary data on demand, and reduce data consumption
- Optimized: Fixed the issue where the page would reset after the first camera permission request on Android, causing an unfriendly interruption
- Optimized: Refined the overall UI visuals for a rounder and lighter appearance
- Optimized: Added EasyTier error prompt when the startup port is occupied on the FnOS version
- Fixed: Custom initial nodes defaulting to the EasyTier maintenance node were not showing in the configurable options list


## 2.1
- 新增：【配置】-自定义路由
- 修复：易组网安卓版本下载、更新问题、去除不支持的开机自启配置
- 修复：易组网windows，MacOS版本桌面图标统一为新图标

<br>

----

- Added: [Config] - Custom Routes
- Fixed: EasyTier-EUI Android download/update issues, removed unsupported auto-start configuration
- Fixed: EasyTier-EUI Windows and macOS desktop icons unified to new icon

##  2.0
- 新增: 易组网使用独立Logo
- 新增: 支持安卓易组网版本
  - 安卓不支持多配置同时运行（受限于 Android 系统限制）
  - 安卓不支持热更新 Easytier 内核（受限于 Android 系统限制）
  - 安卓不支持设置 EasyTier 日志级别（受限于 EasyTier FFI 接口兼容支持）
  - 安卓不支持开机自启
- 新增：【设置】支持设置易组网日志级别
- 新增：【设置】支持清理易组网日志
- 优化: 界面UI优化, 弹窗更清晰, 适配小屏幕组件展示 
- 优化: 后端调用 Easytier 内核实现优化
- 修复: 【配置】保存某些配置项空字符串问题

<br>

----

- New: EasyTier-EUI now uses its own independent logo
- New: Android version support
  - Android does not support running multiple configs simultaneously (limited by Android system restrictions)
  - Android does not support hot-updating the EasyTier core (limited by Android system restrictions)
  - Android does not support setting EasyTier log level (limited by EasyTier FFI interface compatibility)
  - Android does not support auto-start on boot
- New: [Settings] Support setting EasyTier-EUI log level
- New: [Settings] Support clearing EasyTier-EUI logs
- Improved: UI enhancements, clearer dialogs, optimized component display for small screens
- Improved: Backend EasyTier core integration optimized
- Fixed: [Config] Empty string issue when saving certain config items

##  1.6
- 新增：【配置】-代理与转发，支持网段映射
- 修复：【配置】-代理与转发，网段映射为空时，保存启动失败问题
- 新增：支持 musl Linux，支持 x86_64, aarch64, riscv64 架构
- 新增：支持 docker 部署
- 新增：【应用】-【Docker】页面增加docker版本使用说明
- 修复：自定义易组网IP为0.0.0.0时，win、macos版本启动界面加载失败
- 变更：新增配置默认：延迟优先模式、启用通信的加密
- 修复：默认生成relay_network_whitelist = ""，导致不支持转发 ([issue #3](https://github.com/710850609/EasyTier-EUI/issues/3))

<br>

----

- New: [Configuration] - Proxy & Forwarding, now supports subnet mapping
- Fix: [Config] - Proxy & Forward, save startup failure when subnet mapping is empty
- New: Support for musl Linux, supporting x86_64, aarch64, riscv64 architectures
- New: Support for Docker deployment
- New: [Apps] - [Docker] page added with Docker version usage guide
- Fix: Windows and macOS versions failed to load the startup interface when the custom EasyTier-EUI IP was set to 0.0.0.0
- Changed: New default config options: latency-first mode, enable communication encryption
- Fix: Default relay_network_whitelist = "" caused forwarding to fail ([issue #3](https://github.com/710850609/EasyTier-EUI/issues/3))


##  1.5
- 优化：整体视觉优化，更通透，更立体
- 新增：支持国际化，支持多语言
----
- 新增：【设置】页面增加【毛玻璃效果】选项，用户可按需关闭毛玻璃效果，避免老硬件性能不足显示卡顿
- 修复：Linux版本启动提示无可执行权限问题
- 优化：小屏幕适配，默认只显示核心数据，避免信息过载
- 优化：统一多语言命令，飞牛用户版改回：易组网 (用户版)
- 新增：【应用】-【MacOS】页面增加 [socoldkiller/easytier-macos](https://github.com/socoldkiller/easytier-macos) 下载链接
----
- 优化：【应用】官方应用下载优选GitHub加速地址，避免下载失败
- 新增：【设置】页面，【其它】模块增加【辅助GitHub下载】功能，支持前端设备无法下载其它GitHub资源问题
- 修复：配置开机自启时，【设置】页面修改内核日志级别后，未能自动重启，导致设备下线问题
- 优化：【配置】页面控件提示文案展示，监听器增加IPv6地址选项
---
- 新增：支持生成自定义服务IP端口配置，在【设置】页面生成配置后，手动修改重启生效

<br>

----
- Optimized: Overall visual refinement — more transparent, more dimensional
- New: Internationalization support, multi-language support
----
- New: Added Glassmorphism toggle in [Settings], allowing users to disable the frosted glass effect to prevent performance stutter on older hardware
- Fixed: Linux version startup prompt about missing executable permissions
- Optimized: Small screen adaptation — core data displayed by default to avoid information overload
- Optimized: Unified multilingual naming; FeiNiu User Edition reverted to: EasyTier (User Edition)
- New: Added socoldkiller/easytier-macos download link in [Apps] - [macOS]
---- 
- Optimized: Official app downloads in [Apps] now prefer GitHub-accelerated mirrors to avoid download failures
- New: Added GitHub Download Assistant in [Settings] - [Others] module, helping front-end devices that cannot access GitHub resources directly
- Fixed: After changing kernel log level in [Settings], auto-restart failed during boot-startup configuration, causing device to go offline
- Optimized: Improved tooltip copy in [Configuration] page; listener options now include IPv6 address support
----
- New: Support for generating custom service IP/port configurations. Generate in [Settings], then manually edit and restart to apply


## 1.4
- 优化：GitHub资源下载，优化识别处理加速地址返回HTTP状态码 567，导致下载失败情况
- 优化：UI视觉效果，更通透
- 优化：【配置】页面移动端适配
----
- 优化：【配置】页面新增模式关闭逻辑，避免误操作引起报错
- 优化：【节点】页面移动端自适应，默认卡片列表显示，可手动切换到表格显示
- 优化：前端页面显示存储KEY，从etLite改为eui，废弃旧命名，避免歧义。界面会重置默认渲染样式，重新设置即可
- 优化：【节点】页面弹出选择项中，【列选择】改名【数据项选择】避免误解
----
- 优化：飞牛系用户版，改名：易组网(残血版)，避免用户误解
- 优化：【应用】中各官方应用，最新版 改为 预发版
- 优化：【应用-FnOS】 aarch64 按钮，改名 arm64 ，方便更多人理解
----
- 优化：【配置】中编辑文件页面更通透，优化渲染字体，尽量更符合编码视觉习惯，易区分易混淆字符，如：0Ol1
- 优化：【节点】页面延迟时间显示，增加颜色提示，方便用户判断网络延迟是否正常

##  1.3
- 优化：【应用-Linux】使用简介文案，减少歧义误解
- 优化：【应用-IOS】使用简介文案，减少歧义误解
- 优化：【配置】高级设置，【子网代理】增加 CIDR 前缀24长度类型选项
- 修复：【应用-Linux】armv7识别架构错误，下载失败问题，支持版本过低问题
- 新增：【配置】增加支持UI配置【延迟P2P】、【需要P2P】、【socks5端口】、【出口节点】、【实际接收限速】、【端口转发】。独立【代理与转发】新模块
----
- 优化：【设置】安装升级易组网过程，不停止EasyTier服务，避免组网中断
---- 
- 优化：易组网Linux x86_64版本，支持glibc2.28及其以上版本
- 优化：【配置】分享网络，仅导出必要的组网配置
- 优化：提高应用图标清晰度
- 修复：【配置】删除多余的【使用用户态协议栈】选项
- 新增：【配置】增加【禁用UPnP】选项

## 1.2
- 修复：【应用】未能正常下载问题
- 修复：Windows版本易组网自更新，没有启动成功
- 优化：【设置】界面自更新易组网，可查看更新进度
- 新增：飞牛用户版版本，以非root权限运行。默认开启no_tun
- 新增：【设置】界面中 关于 显示是否为用户版

## 1.1
- 优化：【设置】界面一些文案描述优化，避免误解
- 优化：【应用-Linux】易组网界面、使用简介说明优化
- 优化：运行提权逻辑，仅后端服务提权运行
- 优化：Windows版本易组网，不使用UPX压缩，避免杀软误报
- 修复：Linux、Mac版本易组网，在有桌面环境未能自动打开浏览器
- 修复：Linux、Mac版本易组网安装内核时，无法替换，导致安装失败
- 修复：安装内核时，Windows、Linux、Mac系统服务自启，运行中的ET，没停止成功，导致windows版本安装失败，Linux、Mac版本安装后原运行中的ET服务启动失败
----
- 优化：自升级脚本，避免相互阻塞，添加日志记录，方便查看升级过程
- 优化：Linux版本易组网 ctrl+c 关闭逻辑，避免未停止HTTP服务
- 优化：【设置】界面打开自动检查最新版本
- 优化：【设置】界面易组网新版提示
- 优化：【应用】Windows、Linux、MacOS、FnOS版本易组网下载，显示下载进度
- 优化：【应用】EasyTier 管理器下载，显示下载进度
- 修复：【配置】界面普通新增，没有子网代理下拉选项


## 1.0
- 修复：上一个版本易组网下载内置配置失败问题
- 修复：上一个版本【配置】界面节点检测没按可用优先排序问题
- 修复：非飞牛版本切换开机自启，某些情况下重复启动问题
- 优化：GitHub资源下载速度
- 优化：【配置】界面初始节点刷新整合节点下载和节点检测功能
- 优化：【配置-高级-子网代理】界面支持可选当前设备IPv4地址，方便快速设置
- 优化：支持安装路径包含空格
- 优化：【设置-关于】界面优化布局
- 新增：【设置】界面显示EasyTier-EUI安装目录
- 新增：【设置】界面支持自更新
- 新增：【设置-内核】界面支持设置内核日志级别
- 新增：Linux版本【设置】界面 支持关闭 易组网
- 新增：【设置】界面支持查看更新内容
- 变更：【设置】界面不用选择GitHub加速地址，且默认不显示
----
- 优化：【节点】界面默认显示 穿透方式、Nat类型
- 优化：【应用】中各个版本易组网的提示文案
- 优化：【配置】界面高级设置提示文案显示
- 优化：网页标题显示易组网版本号
- 优化：飞牛版本适应系统时间校准导致误识别未运行问题
- 优化：【应用】Linux、安卓、MacOS 的EasyTier GUI下载速度，自动加上加速下载地址
- 新增：【设置】界面支持删除缓存
- 新增：【应用-Linux】界面支持下载EasyTier GUI rpm包
----
- 优化：GitHub资源缓存使用，避免高度访问出现限制
- 优化：【配置】界面提示文案遮挡问题
- 优化：整体视觉样式
- 新增：【设置】界面中，易组网更新日志显示当次版本下载量
----
- 优化：【设置】新增向导初始节点检查逻辑，更合适不同模式新增
- 优化：GitHub加速地址获取
- 修复：Windows, MacOS, Linux 版本易组网重复运行启动问题
- 修复：Linux版本易组网启动、停止脚本运行异常问题
- 修复：飞牛版本易组网自更新支持新依赖更新
----
- 优化：Toast支持换行，优化视觉
- 优化：易组网版本信息增加显示刷新时间
- 优化：【应用-Windows】增加易组网和EasyTier管理器冲突点说明
- 优化：下拉框圆角，优化视觉效果
- 新增：【配置】界面初始节点说明，增加社区节点提供者
----
- 优化：【配置】界面社区节点介绍，适配小屏移动端安全底部，确保能退出弹窗，优化视觉效果
- 优化：【设置】界面易组网版本详情展示，去除表头，使用简易文本代替
----
- 优化：ET、易组网版本获取时间限制逻辑，最小时限1分钟一次
- 修复：Linux版本易组网启动脚本多次启动无法提示重复运行
- 新增：【应用-Linux】界面增加使用简介

## 0.9
- 优化：飞牛系统增加日志记录，方便调试和定位应用运行状态问题
- 优化：优化快速配置和普通配置模式过程
- 优化：Linux版本默认不绑定 127.0.0.1 IP，并尝试本地浏览器打开页面，方便快速访问
- 优化：Windows版本弹UAC授权提示，确保EasyTier内核有管理员权限运行
- 优化：【应用】中各个版本显示中文版本号文案
- 优化：【设置】GitHub加速地址增加测速显示
- 优化：非飞牛版本易组网程序压缩包，独立文件夹，方便不同解压软件解压后文件零散
- 新增：【应用-Linux】界面支持下载易组网Linux版本
- 新增：【设置-关于】界面显示GitHub下载量
- 新增：飞牛版本增加安装向导同意root权限运行提示
- 变更：程序包改名 EasyTier-EUI]()

## 0.8
- 修复：【应用】中各个版本易组网下载失败问题
- 修复：飞牛系统保存配置后开机自启被重置问题
- 修复：GitHub加速下载失败问题
- 修复：window版本某些功能下弹命令窗口问题
- 优化：为兼容Linux不同架构版本运行，统一不使用webview，只提供http服务
- 优化：程序启动时自动申请管理员权限，以确保EasyTier内核有管理员权限运行
- 优化：【设置】界面默认不显示开发者选项
- 新增：支持本地初始节点检测：可用性、延迟、可中转
- 新增：支持 Linux armv7 架构

## 0.7
- 优化：PC端独立窗口模式运行
- 优化：配置页面视觉优化
- 优化：快速设置模式增加自动检测节点是否可用
- 优化：适配EasyTier v2.6.4版本开始，安卓apk下载地址变化
- 优化：【应用】易组网下载支持指定内置配置
- 优化：【应用】EasyTier管理器下载支持指定内置配置
- 优化：pc端改用独立窗口模式运行
- 新增：【应用-FnOS】界面支持下载易组网FnOS版本
- 新增：支持多配置
- 新增：支持开机自启
- 新增：支持配置改名称
- 新增：配置运行的开启、停止
- 新增：分享配置到剪切板

## 0.6
- 修复：网络不好的情况下，获取公共节点报错
- 新增：【设置-关于】界面显示构建版本号
- 新增：【应用-Linux】界面支持下载易组网Linux版本
- 新增：【应用-MacOS】界面支持下载易组网MacOS版本

## 0.5
- 优化：服务重启识别，确保飞牛在线检查正确
- 优化：配置-初始化节点使用txt协议，解决国内网络环境节点识别问题（新特性，在未来某个时间点将下线旧协议，会影响到使用动态节点的组网，请尽量升级新版本）
- 优化：默认配置监听增加 facktcp 协议
- 优化：当内核缺失时，提示用户安装内核
- 优化：默认配置不开启KCP, QUIC协议
- 优化：缩短ET服务关闭等待时间为5秒，提高界面响应速度
- 优化：支持windows版本、Linux-x86_64版本（待验证）、Linux-aarch64版本（待验证）、Linux-riscv64版本（待验证）、Mac-x86_64版本（待验证）、Mac-aarch64版本（待验证）
- 新增：设置-网络新增 加速地址 ghproxy.net, gh.felicity.ac.cn
- 新增：配置-检测节点在当前easytier运行网络是否可用
- 新增：支持下载windows易组网版本

## 0.4
- 修复：更新时，数据被重置问题
- 修复：兼容获取配置初始化节点配置不存在
- 优化：安装默认配置中，给定随机网络名称、网络密码
- 优化：补充魔法DNS说明
- 新增：配置支持设置压缩算法

## 0.3
- 修复：MTU保存值类型错误导致启动失败
- 修复：配置项 enable_ipv6 显示文案和保存值歧义
- 修复：配置项 enable_encryption 显示文案和保存值歧义
- 优化：配置页面视觉优化
- 优化：设置-关于显示
- 优化：节点NAT类型转译细化类型
- 优化：配置-初始节点显示文案，显示节点使用的GitHub加速地址
- 优化：UI重启服务，飞牛误识别服务异常退出问题
- 新增：设置-内核支持检查、安装版本
- 新增：设置-网络支持设置github加速地址
- 新增：配置支持线程数、加密算法、转发白名单配置选项
- 新增：支持初始节点数据刷新
- 新增：支持引导下载windows gui版本

## 0.2
- 修复：编辑配置文件删减选项后，未保存生效的问题
- 修复：节点列表中，协议过长显示不全的问题
- 新增：可视化配置TUN接口名称
- 新增：可视化配置MTU

## 0.1
- 初版