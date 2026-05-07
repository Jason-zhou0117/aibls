# settings.py
"""
全局配置模块 - 避免循环引用
"""

import os
import sys


def get_app_dir():
    """获取应用程序根目录（项目根目录）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的环境
        return os.path.dirname(sys.executable)
    else:
        # 正常 Python 环境
        # 当前文件在 aibls 目录下，向上取一层就是项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)


# ==================== 路径配置 ====================
# 项目根目录
APP_ROOT = get_app_dir()

# Docker 环境检测（通过环境变量）
IN_DOCKER = os.environ.get('DOCKER_ENV', 'false').lower() == 'true'

# 嵌入式 Python 检测（Windows 嵌入式运行）
RUNTIME_DIR = os.path.join(APP_ROOT, 'runtime')
IN_EMBEDDED = os.path.exists(RUNTIME_DIR) and os.path.exists(os.path.join(RUNTIME_DIR, 'python.exe'))

if IN_DOCKER:
    # Docker 环境：使用容器内的路径
    APP_ROOT = '/app'
    print("[Settings] 运行环境: Docker")
elif IN_EMBEDDED:
    # Windows 嵌入式运行
    print(f"[Settings] 运行环境: 嵌入式 (Windows)")
    print(f"[Settings] APP_ROOT: {APP_ROOT}")
else:
    # 开发环境（PyCharm）
    print(f"[Settings] 运行环境: 开发环境")
    print(f"[Settings] APP_ROOT: {APP_ROOT}")

# 子目录路径
STATIC_DIR = os.path.join(APP_ROOT, 'web', 'static')
TEMPLATE_DIR = os.path.join(APP_ROOT, 'web', 'templates')
VIDEO_DIR = os.path.join(APP_ROOT, 'web', 'static', 'videos')
# VIDEO_DIR = os.path.join(STATIC_DIR, 'video')        # 视频文件目录（Docker 中挂载）
LOG_DIR = os.path.join(APP_ROOT, 'logs')

# 兼容旧版视频目录（如果 video 目录不存在，尝试使用 web/static/videos）
if not os.path.exists(VIDEO_DIR):
    VIDEO_DIR = os.path.join(APP_ROOT, 'web', 'static', 'videos')

# 嵌入式Python的路径（仅 Windows 嵌入式使用）
PYTHON_EXE = os.path.join(RUNTIME_DIR, 'python.exe') if os.path.exists(RUNTIME_DIR) else 'python'

# ==================== 运行环境判断 ====================
# 是否为嵌入式运行（Windows）
IS_EMBEDDED = IN_EMBEDDED

# 是否为调试模式
DEBUG_MODE = not (IS_EMBEDDED or IN_DOCKER)

# ==================== 确保目录存在 ====================

def ensure_directories():
    """确保必要的目录存在"""
    dirs = [LOG_DIR, VIDEO_DIR]
    for d in dirs:
        if not os.path.exists(d):
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                print(f"[Settings] 创建目录失败 {d}: {e}")

# 自动创建目录（仅在非 Docker 环境或目录可写时）
if not IN_DOCKER:
    ensure_directories()
else:
    print(f"[Settings] Docker 环境，跳过目录创建（使用挂载卷）")
    print(f"[Settings] VIDEO_DIR: {VIDEO_DIR}")
    print(f"[Settings] LOG_DIR: {LOG_DIR}")

# 调试输出
print(f"[Settings] STATIC_DIR: {STATIC_DIR}")
print(f"[Settings] TEMPLATE_DIR: {TEMPLATE_DIR}")
print(f"[Settings] VIDEO_DIR: {VIDEO_DIR}")
print(f"[Settings] LOG_DIR: {LOG_DIR}")
print(f"[Settings] IS_EMBEDDED: {IS_EMBEDDED}")
print(f"[Settings] IN_DOCKER: {IN_DOCKER}")
print(f"[Settings] DEBUG_MODE: {DEBUG_MODE}")