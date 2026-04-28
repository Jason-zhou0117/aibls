@echo off
chcp 65001 >nul
title BiliMon 弹幕监控系统

:: 切换到当前目录
cd /d "%~dp0"

:: 设置Python路径为嵌入式Python
set PATH=%~dp0runtime;%~dp0runtime\Scripts;%PATH%
set PYTHONHOME=%~dp0runtime

:: 创建必要目录
if not exist "logs" mkdir logs
if not exist "sessions" mkdir sessions
if not exist "web\static\videos" mkdir web\static\videos

echo ========================================
echo    BiliMon 弹幕监控系统
echo ========================================
echo.
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 可停止服务
echo.
echo ========================================

:: 启动服务
.\runtime\python.exe app.py

pause