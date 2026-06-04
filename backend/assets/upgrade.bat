@echo off
if "%~1"=="" (
    echo 用法: %~nx0 "安装路径"
    exit /b 1
)

set "APP_DIR=%~1"
set "UPDATE_DIR=%APP_DIR%\_update"

:wait
taskkill /f /im "EasyTier-EUI.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
tasklist /fi "imagename eq EasyTier-EUI.exe" | find /i "EasyTier-EUI.exe" >nul
if not errorlevel 1 goto wait

:: 替换文件
move /y "%UPDATE_DIR%\EasyTier-EUI.exe" "%APP_DIR%\EasyTier-EUI.exe"
move /y "%UPDATE_DIR%\_internal" "%APP_DIR%\_internal"

:: 删除 _update 文件夹（/s 删除子目录和文件，/q 安静模式不确认）
rmdir /s /q "%UPDATE_DIR%"

:: 启动
start "" "%APP_DIR%\EasyTier-EUI.exe"
