# aibls/generator_manager.py
"""独立的生成器管理器 - 避免循环导入"""

from aibls.services.danmu_handler import AsyncMessageGenerator
from aibls.stock_io import message_queue

_generator = None
_app = None


def init_generator(app):
    """在 app 初始化完成后调用，设置生成器"""
    global _generator, _app
    _app = app
    _generator = AsyncMessageGenerator(message_queue, app=app)
    return _generator


def get_generator():
    """获取生成器实例"""
    global _generator
    return _generator


def reset_generator():
    """重置生成器（销毁旧的，创建新的）"""
    global _generator, _app

    # 停止旧的
    if _generator:
        _generator.stop()

    # 创建新的
    _generator = AsyncMessageGenerator(message_queue, app=_app)
    return _generator