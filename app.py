# app.py
# -*- coding: utf-8 -*-
"""
BiliMon 弹幕监控系统 - 主入口
"""

import os
import sys
import logging
import time
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask, request, Response, jsonify
from flask_session import Session

from aibls.generator_manager import init_generator
from aibls.services.message_consumer import MessageConsumer

# ==================== 环境初始化 ====================

# 将当前目录添加到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 从 aibls 包导入
from aibls import (
    get_app_config,
    init_db,
    socketio,
    message_queue,
    db
)
from aibls.settings import APP_ROOT, IS_EMBEDDED, DEBUG_MODE, LOG_DIR, STATIC_DIR, TEMPLATE_DIR
from aibls.views import user_api, room_api, live_api, vip_api,gift_api
from aibls.views.live_route import generator

# 切换到项目根目录
os.chdir(APP_ROOT)


# ==================== 创建应用 ====================

def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__,
                static_folder=STATIC_DIR,
                template_folder=TEMPLATE_DIR)

    # 加载配置
    app_config = get_app_config()
    app.config.from_object(app_config)
    app.debug = DEBUG_MODE

    # 初始化扩展
    Session(app)
    init_db(app)  # 初始化数据库（只会执行一次建表）

    # 注册蓝图和日志
    register_blueprint(app)
    register_log(app)

    #迁移数据
    # with app.app_context():
    #     from aibls.utils.migrate_json_to_db import migrate_json_to_db
    #     migrate_json_to_db()
    return app


def register_blueprint(app: Flask):
    """注册所有蓝图"""
    app.register_blueprint(user_api)
    app.register_blueprint(room_api)
    app.register_blueprint(live_api)
    app.register_blueprint(vip_api)
    app.register_blueprint(gift_api)

    print_registered_routes(app)


def print_registered_routes(app):
    """打印已注册的路由（调试用）"""
    print("\n" + "=" * 60)
    print("当前已成功注册的路由列表：")
    print("=" * 60)
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.endpoint:30s} | {methods:15s} | {rule.rule}")
    print("=" * 60 + "\n")


def register_log(app: Flask):
    """配置日志"""
    # 清除默认的处理器，避免重复
    app.logger.handlers.clear()

    # 设置根日志级别
    app.logger.setLevel(logging.DEBUG)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. 文件处理器（记录 INFO 及以上级别）
    str_day = time.strftime("%Y-%m-%d", time.localtime())
    log_dir = os.path.join(APP_ROOT, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f'log-{str_day}.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)  # 文件只记录 INFO 及以上
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    # 2. 控制台处理器（记录 DEBUG 及以上级别，便于调试）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 控制台记录所有
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    # 3. 错误文件处理器（单独记录错误）
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, f'error-{str_day}.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)  # 只记录 ERROR 及以上
    error_handler.setFormatter(formatter)
    app.logger.addHandler(error_handler)

    app.logger.info("日志系统初始化完成")


# ==================== 初始化应用 ====================

app = create_app()
# ✅ 立即初始化 generator
init_generator(app)

# 初始化消费者并传入 app
message_consumer = MessageConsumer(app)
# ✅ 启动消费者线程
import threading
consumer_thread = threading.Thread(target=message_consumer.run, daemon=True)
consumer_thread.start()
app.logger.info("消息消费者线程已启动")

# SocketIO 初始化（必须在 app 创建之后）
socketio.init_app(app,
                  cors_allowed_origins="*",
                  async_mode='gevent',
                  logger=True,
                  engineio_logger=True)


# ==================== 路由 ====================
@app.route('/debug/routes')
def debug_routes():
    """调试路由 - 查看所有路由"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'url': str(rule),
            'methods': list(rule.methods)
        })
    return jsonify({
        'total_routes': len(routes),
        'routes': routes,
        'blueprints': list(app.blueprints.keys())
    })


# ==================== 启动入口 ====================

if __name__ == "__main__":
    try:
        PORT = 5001
        print("=" * 60)
        print(f"运行环境: {'嵌入式运行' if IS_EMBEDDED else '开发环境'}")
        print(f"项目目录: {APP_ROOT}")
        print(f"启动服务器...")
        print(f"队列大小: {message_queue.qsize()}")
        print("=" * 60)
        print(f"访问地址: http://localhost:{PORT}")
        print("=" * 60)

        # 根据环境选择运行参数
        if DEBUG_MODE:
            # 开发环境（PyCharm）
            socketio.run(app,
                         debug=True,
                         port=PORT,
                         use_reloader=False,
                         log_output=True)
        else:
            # 生产环境（嵌入式）
            socketio.run(app,
                         debug=False,
                         port=PORT,
                         allow_unsafe_werkzeug=True,
                         use_reloader=False)

    except KeyboardInterrupt:
        print("\n👋 正在关闭服务器...")
        generator.stop()
        print("服务器已关闭")