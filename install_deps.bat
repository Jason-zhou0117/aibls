@echo off
chcp 65001 >nul
echo ========================================
echo    正在安装依赖包到嵌入式Python
echo ========================================
echo.

:: 升级 pip（可选）
.\runtime\python.exe -m pip install --upgrade pip

echo.
echo [*] 正在安装项目依赖包...
echo.

:: 使用清华镜像源加速
.\runtime\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ========================================
echo    安装完成！
echo ========================================
pause