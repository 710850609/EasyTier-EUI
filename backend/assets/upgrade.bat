@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo 用法: %~nx0 "安装路径"
    exit /b 1
)

set "APP_DIR=%~1"
set "UPDATE_DIR=%APP_DIR%\_update"
set "LOG_DIR=%APP_DIR%\logs"
set "LOG_FILE=%LOG_DIR%\app.log"
set "SCRIPT_NAME=upgrade.bat"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

goto :main

:: 统一日志输出（使用 wmic 获取 yyyy-MM-dd HH:mm:ss，跨语言区域一致）
:log
for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value 2^>nul ^| find "="') do set "DT=%%i"
set "TS=%DT:~0,4%-%DT:~4,2%-%DT:~6,2% %DT:~8,2%:%DT:~10,2%:%DT:~12,2%"
echo %TS% - [%SCRIPT_NAME%] - %~1
echo %TS% - [%SCRIPT_NAME%] - %~1 >> "%LOG_FILE%"
goto :eof

:sleep
REM 可靠睡眠等待，参数为秒数
REM 用法: call :sleep 5
powershell -NoProfile -Command "Start-Sleep -Seconds %~1"
goto :eof

:main
call :log "执行"

:: 等待旧进程完全退出（最多等 10 秒）
set WAIT_SEC=0
:wait_exit
tasklist /fi "imagename eq EasyTier-EUI.exe" 2>nul | find /i "EasyTier-EUI.exe" >nul
if errorlevel 1 goto proc_exited
if !WAIT_SEC! geq 10 (
    call :log "等待超时，强制终止旧进程"
    taskkill /f /im "EasyTier-EUI.exe" >nul 2>&1
    call :sleep 2
    goto proc_exited
)
call :log "等待旧进程退出... (!WAIT_SEC! 秒)"
call :sleep 1
set /a WAIT_SEC+=1
goto wait_exit

:proc_exited
call :log "旧进程已退出，开始替换文件"

:: 移动新文件
if exist "%UPDATE_DIR%\EasyTier-EUI.exe" (
    move /y "%UPDATE_DIR%\EasyTier-EUI.exe" "%APP_DIR%\EasyTier-EUI.exe" >nul 2>&1
    if errorlevel 1 (
        call :log "[错误] 主程序替换失败，文件可能被占用"
        exit /b 1
    )
    call :log "二进制已替换"
) else (
    call :log "[错误] 更新文件不存在 %UPDATE_DIR%\EasyTier-EUI.exe"
    exit /b 1
)

:: 清理更新目录
rmdir /s /q "%UPDATE_DIR%" >nul 2>&1
if exist "%UPDATE_DIR%" (
    call :log "[警告] 更新目录未能完全删除，但程序已更新"
) else (
    call :log "更新目录已清理"
)

:: 启动
call :log "启动 EasyTier-EUI..."
start "" "%APP_DIR%\EasyTier-EUI.exe"

call :log "完成"

:: 删除脚本自身
call :sleep 2
start /b "" cmd /c "del /f /q "%~f0""