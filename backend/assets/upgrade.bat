@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo 用法: %~nx0 "安装路径"
    exit /b 1
)

set "APP_DIR=%~1"
set "UPDATE_DIR=%APP_DIR%\_update"
set "LOG_DIR=%APP_DIR%\logs"
set "LOG_FILE=%LOG_DIR%\app.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: 通过 PowerShell Tee 同时输出到终端和日志（参考 start.sh）
if not defined _UPGRADE_TEE_RUN (
    set "_UPGRADE_TEE_RUN=1"
    "%~f0" %* 2>&1 | powershell -NoProfile -Command "$input | ForEach-Object { $_; Add-Content -Path '%LOG_FILE%' -Value $_ }"
    exit /b !errorlevel!
)

echo %date% %time% === upgrade.bat 执行 ===

:: 等待旧进程完全退出（最多等 30 秒）
set WAIT_SEC=0
:wait_exit
tasklist /fi "imagename eq EasyTier-EUI.exe" 2>nul | find /i "EasyTier-EUI.exe" >nul
if errorlevel 1 goto proc_exited
if !WAIT_SEC! geq 3 (
    echo 等待超时，强制终止旧进程
    taskkill /f /im "EasyTier-EUI.exe" >nul 2>&1
    timeout /t 3 /nobreak >nul
    goto proc_exited
)
echo 等待旧进程退出... (!WAIT_SEC! 秒)
timeout /t 1 /nobreak >nul
set /a WAIT_SEC+=1
goto wait_exit

:proc_exited
echo 旧进程已退出，开始替换文件

:: 移动新文件
if exist "%UPDATE_DIR%\EasyTier-EUI.exe" (
    move /y "%UPDATE_DIR%\EasyTier-EUI.exe" "%APP_DIR%\EasyTier-EUI.exe" >nul 2>&1
    if errorlevel 1 (
        echo [错误] 主程序替换失败，文件可能被占用
        exit /b 1
    )
    echo 二进制已替换
) else (
    echo [错误] 更新文件不存在 %UPDATE_DIR%\EasyTier-EUI.exe
    exit /b 1
)

:: 清理更新目录
rmdir /s /q "%UPDATE_DIR%" >nul 2>&1
if exist "%UPDATE_DIR%" (
    echo [警告] 更新目录未能完全删除，但程序已更新
) else (
    echo 更新目录已清理
)

:: 启动
echo 启动 EasyTier-EUI...
start "" "%APP_DIR%\EasyTier-EUI.exe"

echo %date% %time% upgrade.bat 完成