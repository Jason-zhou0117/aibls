# settings.py
"""
全局配置模块 - 避免循环引用
"""

import os
import sys

def get_app_dir():
    """获取应用程序根目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# ==================== 路径配置 ====================

# 项目根目录
APP_ROOT = get_app_dir()

# 嵌入式Python的路径（用于脚本）
RUNTIME_DIR = os.path.join(APP_ROOT, 'runtime')
PYTHON_EXE = os.path.join(RUNTIME_DIR, 'python.exe') if os.path.exists(RUNTIME_DIR) else 'python'

# 子目录路径
STATIC_DIR = os.path.join(APP_ROOT, 'web', 'static')
TEMPLATE_DIR = os.path.join(APP_ROOT, 'web', 'templates')
VIDEO_DIR = os.path.join(APP_ROOT, 'web', 'static', 'videos')
CONFIG_DIR = os.path.join(APP_ROOT, 'config')
LOG_DIR = os.path.join(APP_ROOT, 'logs')
ROOM_DIR = os.path.join(APP_ROOT, 'rooms')
SESSION_DIR = os.path.join(APP_ROOT, 'sessions')

# ==================== 运行环境判断 ====================

# 是否为嵌入式运行
IS_EMBEDDED = os.path.exists(RUNTIME_DIR) and os.path.exists(os.path.join(RUNTIME_DIR, 'python.exe'))

# 方法2（备用）：检查是否从 runtime 目录启动
if not IS_EMBEDDED:
    # 检查当前 Python 解释器路径是否包含 'runtime'
    IS_EMBEDDED = 'runtime' in sys.executable.lower()

# 调试输出（可以暂时加上，确认后删除）
print(f"[DEBUG] APP_ROOT: {APP_ROOT}")
print(f"[DEBUG] RUNTIME_DIR: {RUNTIME_DIR}")
print(f"[DEBUG] sys.executable: {sys.executable}")
print(f"[DEBUG] IS_EMBEDDED: {IS_EMBEDDED}")

# 是否为调试模式
DEBUG_MODE = not IS_EMBEDDED

# ==================== 确保目录存在 ====================

def ensure_directories():
    """确保必要的目录存在"""
    dirs = [SESSION_DIR, LOG_DIR, VIDEO_DIR, CONFIG_DIR,ROOM_DIR]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

# 自动创建目录
ensure_directories()