@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 启动服务（最小化窗口）
start /min "BiliMon服务" cmd /c "启动服务.bat"

:: 等待服务启动
timeout /t 3 /nobreak >nul

:: 打开浏览器
start http://localhost:5000/index

echo.
echo ========================================
echo     BiliMon 已启动！
echo     浏览器已自动打开
echo     服务窗口已最小化到任务栏
echo ========================================
echo.