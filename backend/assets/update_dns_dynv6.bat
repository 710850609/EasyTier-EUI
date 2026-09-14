@echo off
chcp 65001 >nul 2>nul
setlocal enabledelayedexpansion
:: EasyTier-EUI dynv6 DNS TXT 记录更新脚本 (Windows)
:: 用法: update_dns_dynv6.bat <protocol> <publicIp> <publicPort> <zoneName> <subdomain> [apiToken]
:: 示例: update_dns_dynv6.bat "tcp" "1.2.3.4" "8080" "example.com" "_acme-challenge"
:: 支持最多 3 次重试

set "DYNV6_API=https://dynv6.com/api/v2"
set "SCRIPT_NAME=update_dns_dynv6.bat"
set "MAX_RETRY=3"
set "RETRY_DELAY=2"
set "TEMP_JSON=%TEMP%\dynv6_update_%RANDOM%.json"
set "TEMP_ERR=%TEMP%\dynv6_err_%RANDOM%.txt"
set "TEMP_BODY=%TEMP%\dynv6_body_%RANDOM%.txt"

if "%~4"=="" (
    call :log "用法: %~nx0 <protocol> <publicIp> <publicPort> <zoneName> <subdomain> [apiToken]"
    call :log "示例: %~nx0 \"tcp\" \"1.2.3.4\" \"8080\" \"example.com\" \"_acme-challenge\""
    exit /b 1
)

set "PROTOCOL=%~1"
set "PUBLIC_IP=%~2"
set "PUBLIC_PORT=%~3"
set "ZONE_NAME=%~4"
set "SUBDOMAIN=%~5"

if not "%~6"=="" (
    set "TOKEN=%~6"
) else if defined DYNV6_API_TOKEN (
    set "TOKEN=%DYNV6_API_TOKEN%"
) else (
    call :log "错误: 未设置 apiToken 参数或环境变量 DYNV6_API_TOKEN"
    exit /b 1
)

set "TXT_VALUE=%PROTOCOL%://%PUBLIC_IP%:%PUBLIC_PORT%"
set "FULL_RECORD_NAME=%SUBDOMAIN%.%ZONE_NAME%"

call :log "开始更新 DNS TXT 记录"
call :log "  协议: %PROTOCOL%"
call :log "  公网IP: %PUBLIC_IP%"
call :log "  公网端口: %PUBLIC_PORT%"
call :log "  域名: %ZONE_NAME%"
call :log "  子域名: %SUBDOMAIN%"
call :log "  完整记录名: %FULL_RECORD_NAME%"
call :log "  记录值(URI): %TXT_VALUE%"

:: ============================================================
:: Step 1: 根据域名查询 zoneId
:: ============================================================
call :log "查询 Zone ID..."
call :retry_get "%DYNV6_API%/zones" || goto :cleanup_fail

call :log "  Zone API 返回: "
type "%TEMP_JSON%"
for /f %%i in ('powershell -NoProfile -Command "$z=Get-Content '%TEMP_JSON%' -Raw|ConvertFrom-Json|Where-Object{$_.name -eq '%ZONE_NAME%'}; if($z){$z.id}"') do set "ZONE_ID=%%i"
if "%ZONE_ID%"=="" (
    call :log "错误: 未找到域名 %ZONE_NAME% 对应的 Zone"
    goto :cleanup_fail
)
call :log "  Zone ID: %ZONE_ID%"

:: ============================================================
:: Step 2: 查询已有同名 TXT 记录，有则更新，无则新增
:: ============================================================
call :log "查询已有 TXT 记录..."
call :retry_get "%DYNV6_API%/zones/%ZONE_ID%/records" || goto :cleanup_fail
call :log "  Records API 返回: "
type "%TEMP_JSON%"

set "HAS_RECORDS="
for /f %%i in ('powershell -NoProfile -Command "$r=(Get-Content '%TEMP_JSON%' -Raw|ConvertFrom-Json|Where-Object{$_.name -eq '%SUBDOMAIN%' -and $_.type -eq 'TXT'}); if($r){$r.id}"') do (
    set "HAS_RECORDS=1"
    call :log "更新已有 TXT 记录: ID=%%i"
    (echo {"data":"%TXT_VALUE%"}) > "%TEMP_BODY%"
    call :retry_patch "%DYNV6_API%/zones/%ZONE_ID%/records/%%i" || goto :cleanup_fail
    for /f "usebackq delims=" %%j in ("%TEMP_JSON%") do call :log "  更新成功: %%j"
)

if not defined HAS_RECORDS (
    call :log "  未找到同名 TXT 记录，新增记录..."
    (echo {"name":"%SUBDOMAIN%","type":"TXT","data":"%TXT_VALUE%"}) > "%TEMP_BODY%"
    call :retry_post "%DYNV6_API%/zones/%ZONE_ID%/records" || goto :cleanup_fail
    for /f "usebackq delims=" %%j in ("%TEMP_JSON%") do call :log "  新增成功: %%j"
)

call :log "完成"
del "%TEMP_JSON%" 2>nul
del "%TEMP_ERR%" 2>nul
del "%TEMP_BODY%" 2>nul
exit /b 0

:: ============================================================
:: 子程序
:: ============================================================

:log
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "LTS=%%I"
set "LTS=%LTS:~0,4%-%LTS:~4,2%-%LTS:~6,2% %LTS:~8,2%:%LTS:~10,2%:%LTS:~12,2%"
set "LMSG=%*"
set "LMSG=!LMSG:"=!"
echo %LTS% [%SCRIPT_NAME%] !LMSG!
goto :eof

:: HTTP GET 带重试，结果写入 %TEMP_JSON%
:retry_get
set "RURL=%~1"
set /a N=0
:retry_get_loop
set /a N+=1
curl -sfL -H "Authorization: Bearer %TOKEN%" "%RURL%" > "%TEMP_JSON%" 2>"%TEMP_ERR%"
if not errorlevel 1 exit /b 0
call :log "GET %RURL% 第!N!次失败, curl exit=!ERRORLEVEL!"
if exist "%TEMP_ERR%" for /f "usebackq delims=" %%e in ("%TEMP_ERR%") do call :log "  curl error: %%e"
if !N! lss %MAX_RETRY% (
    call :log "  %RETRY_DELAY%秒后重试..."
    timeout /t %RETRY_DELAY% /nobreak >nul
    goto :retry_get_loop
)
call :log "错误: GET 已重试%MAX_RETRY%次，全部失败"
exit /b 1

:: HTTP POST 带重试，结果写入 %TEMP_JSON%
:retry_post
set "RURL=%~1"
call :log "  POST %RURL%"
call :log "  请求体: "
type "%TEMP_BODY%"
set /a N=0
:retry_post_loop
set /a N+=1
curl -sfL -X POST -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "@%TEMP_BODY%" "%RURL%" > "%TEMP_JSON%" 2>"%TEMP_ERR%"
if not errorlevel 1 exit /b 0
call :log "POST 第!N!次失败, curl exit=!ERRORLEVEL!"
if exist "%TEMP_ERR%" for /f "usebackq delims=" %%e in ("%TEMP_ERR%") do call :log "  curl error: %%e"
if !N! lss %MAX_RETRY% (
    call :log "  %RETRY_DELAY%秒后重试..."
    timeout /t %RETRY_DELAY% /nobreak >nul
    goto :retry_post_loop
)
call :log "错误: POST 已重试%MAX_RETRY%次，全部失败"
exit /b 1

:: HTTP PATCH 带重试，结果写入 %TEMP_JSON%
:retry_patch
set "RURL=%~1"
call :log "  PATCH %RURL%"
call :log "  请求体: "
type "%TEMP_BODY%"
set /a N=0
:retry_patch_loop
set /a N+=1
curl -sfL -X PATCH -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "@%TEMP_BODY%" "%RURL%" > "%TEMP_JSON%" 2>"%TEMP_ERR%"
if not errorlevel 1 exit /b 0
call :log "PATCH 第!N!次失败, curl exit=!ERRORLEVEL!"
if exist "%TEMP_ERR%" for /f "usebackq delims=" %%e in ("%TEMP_ERR%") do call :log "  curl error: %%e"
if !N! lss %MAX_RETRY% (
    call :log "  %RETRY_DELAY%秒后重试..."
    timeout /t %RETRY_DELAY% /nobreak >nul
    goto :retry_patch_loop
)
call :log "错误: PATCH 已重试%MAX_RETRY%次，全部失败"
exit /b 1

:cleanup_fail
del "%TEMP_JSON%" 2>nul
del "%TEMP_ERR%" 2>nul
del "%TEMP_BODY%" 2>nul
exit /b 1