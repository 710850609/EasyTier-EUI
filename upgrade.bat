@echo off
:wait
taskkill /f /im "EasyTier-EUI.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
tasklist /fi "imagename eq EasyTier-EUI.exe" | find /i "EasyTier-EUI.exe" >nul
if not errorlevel 1 goto wait

:: 替换文件
move /y "%~dp0_update\EasyTier-EUI.exe" "%~dp0EasyTier-EUI.exe"
move /y "%~dp0_update\_internal" "%~dp0_internal"

:: 启动
start "" "%~dp0EasyTier-EUI.exe"
rem del "%~f0"
