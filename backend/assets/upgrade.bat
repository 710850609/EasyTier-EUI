@echo off
if "%~1"=="" (
    echo 用法: %~nx0 "安装路径"
    exit /b 1
)

set "APP_DIR=%~1"
set "UPDATE_DIR=%APP_DIR%\_update"

:: 循环结束进程，并等待句柄释放
:wait
taskkill /f /im "EasyTier-EUI.exe" >nul 2>&1
timeout /t 2 /nobreak >nul
tasklist /fi "imagename eq EasyTier-EUI.exe" | find /i "EasyTier-EUI.exe" >nul
if not errorlevel 1 goto wait

:: 额外多等 3 秒，确保杀毒软件/系统释放锁
timeout /t 3 /nobreak >nul

:: 先处理 _internal：如果存在，先重命名/删除旧的
@REM if exist "%APP_DIR%\_internal" (
@REM     rmdir /s /q "%APP_DIR%\_internal.old" >nul 2>&1
@REM     move /y "%APP_DIR%\_internal" "%APP_DIR%\_internal.old" >nul
@REM )

:: 移动新文件（加错误判断）
move /y "%UPDATE_DIR%\EasyTier-EUI.exe" "%APP_DIR%\EasyTier-EUI.exe" >nul
if errorlevel 1 (
    echo [错误] 主程序替换失败，文件可能被占用
    exit /b 1
)

@REM move /y "%UPDATE_DIR%\_internal" "%APP_DIR%\_internal" >nul
@REM if errorlevel 1 (
@REM     echo [错误] 依赖目录替换失败
@REM     exit /b 1
@REM )

:: 清理更新目录
rmdir /s /q "%UPDATE_DIR%" >nul 2>&1
if exist "%UPDATE_DIR%" (
    echo [警告] 更新目录未能完全删除，但程序已更新
)

:: 启动
start "" "%APP_DIR%\EasyTier-EUI.exe"