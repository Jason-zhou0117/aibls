@echo off
chcp 65001 >nul
title 启动 BiliMon

:: 切换到当前目录
cd /d "%~dp0"

:: 使用完整路径调用启动服务.bat
start /min "BiliMon服务" cmd /c "%~dp0启动服务.bat"

:: 等待服务启动
echo 等待服务启动...
timeout /t 5 /nobreak >nul

:: 打开浏览器
start http://localhost:5001

echo.
echo ========================================
echo     BiliMon 已启动！
echo     浏览器已自动打开
echo ========================================
echo.
pause