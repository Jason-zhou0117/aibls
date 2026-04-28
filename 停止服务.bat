@echo off
chcp 65001 >nul
title 停止 BiliMon

echo ========================================
echo    正在停止 BiliMon 服务
echo ========================================

:: 关闭占用5000端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| find ":5000" ^| find "LISTENING"') do (
    taskkill /PID %%a /f >nul 2>&1
)

timeout /t 2 /nobreak >nul
echo.
echo 服务已停止
echo.
pause