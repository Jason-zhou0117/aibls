# app.py
# -*- coding: utf-8 -*-
"""
BiliMon 弹幕监控系统 - 主入口
"""

import os
import sys
import logging
import time
import threading
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_session import Session


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
from aibls.settings import (
    APP_ROOT,
    IS_EMBEDDED,
    IN_DOCKER,
    DEBUG_MODE,
    STATIC_DIR,
    TEMPLATE_DIR,
    LOG_DIR
)

# ==================== 环境初始化 ====================


# 切换到项目根目录
if os.path.exists(APP_ROOT):
    os.chdir(APP_ROOT)
    print(f"[App] 切换工作目录到: {APP_ROOT}")

from aibls.views import user_api, room_api, live_api, vip_api, gift_api, stat_api, logoff_api
from aibls.generator_manager import init_generator, stop_generator
from aibls.services.message_consumer import MessageConsumer
from aibls.scheduler import danmaku_scheduler
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

    # 初始化数据库（只会执行一次建表）
    init_db(app)

    # 将 Session 指向数据库
    app.config['SESSION_SQLALCHEMY'] = db

    # 初始化 Session 扩展
    Session(app)

    # 注册蓝图和日志
    register_blueprint(app)
    register_log(app)

    return app


def register_blueprint(app: Flask):
    """注册所有蓝图"""
    app.register_blueprint(user_api)
    app.register_blueprint(room_api)
    app.register_blueprint(live_api)
    app.register_blueprint(vip_api)
    app.register_blueprint(gift_api)
    app.register_blueprint(stat_api)
    app.register_blueprint(logoff_api)

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

    # 确保日志目录存在（Docker 中可能由卷挂载）
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_writable = os.access(LOG_DIR, os.W_OK)
    except Exception as e:
        log_writable = False
        print(f"[App] 日志目录创建失败: {e}")

    if log_writable:
        # 1. 文件处理器（记录 INFO 及以上级别）
        str_day = time.strftime("%Y-%m-%d", time.localtime())
        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, f'log-{str_day}.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

        # 2. 错误文件处理器（单独记录错误）
        error_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, f'error-{str_day}.log'),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        app.logger.addHandler(error_handler)
    else:
        print(f"[App] 日志目录不可写，跳过文件日志: {LOG_DIR}")

    # 3. 控制台处理器（所有环境都需要）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    app.logger.info("日志系统初始化完成")
    if IN_DOCKER:
        app.logger.info("运行环境: Docker")
    elif IS_EMBEDDED:
        app.logger.info("运行环境: Windows 嵌入式")
    else:
        app.logger.info("运行环境: 开发环境")


# ==================== 初始化应用 ====================

app = create_app()

# 初始化 generator
init_generator(app)

# 初始化消费者并传入 app
message_consumer = MessageConsumer(app)

# 启动消费者线程
consumer_thread = threading.Thread(target=message_consumer.run, daemon=True, name="MessageConsumer")
consumer_thread.start()
app.logger.info("消息消费者线程已启动")

# SocketIO 初始化（必须在 app 创建之后）
socketio.init_app(app,
                  cors_allowed_origins="*",
                  async_mode='gevent',
                  logger=True,
                  engineio_logger=True)


# 初始化定时发送弹幕调度器
danmaku_scheduler.init_app(app)
danmaku_scheduler.start()
app.logger.info("定时发送弹幕调度器已启动")

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


@app.route('/health')
def health_check():
    """健康检查接口（用于 Docker 健康检查）"""
    return jsonify({
        'status': 'ok',
        'environment': 'docker' if IN_DOCKER else ('embedded' if IS_EMBEDDED else 'development'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })


# ==================== 启动入口 ====================

if __name__ == "__main__":
    try:
        # 端口配置（支持环境变量）
        PORT = int(os.environ.get('PORT', 5001))
        HOST = os.environ.get('HOST', '0.0.0.0')

        print("=" * 60)
        if IN_DOCKER:
            print("运行环境: Docker 容器")
        elif IS_EMBEDDED:
            print("运行环境: Windows 嵌入式运行")
        else:
            print("运行环境: 开发环境 (PyCharm)")
        print(f"项目目录: {APP_ROOT}")
        print(f"启动服务器...")
        print(f"队列大小: {message_queue.qsize()}")
        print("=" * 60)
        print(f"访问地址: http://{HOST}:{PORT}")
        if IN_DOCKER:
            print(f"容器内地址: http://localhost:{PORT}")
        print("=" * 60)

        # 根据环境选择运行参数
        if IN_DOCKER:
            # Docker 环境：生产模式，禁用 debug
            socketio.run(app,
                         host=HOST,
                         port=PORT,
                         debug=False,
                         allow_unsafe_werkzeug=True,
                         use_reloader=False)
        elif DEBUG_MODE:
            # 开发环境（PyCharm）
            socketio.run(app,
                         debug=True,
                         host='127.0.0.1',
                         port=PORT,
                         use_reloader=False,
                         log_output=True)
        else:
            # 生产环境（Windows 嵌入式）
            socketio.run(app,
                         debug=False,
                         host='127.0.0.1',
                         port=PORT,
                         allow_unsafe_werkzeug=True,
                         use_reloader=False)

    except KeyboardInterrupt:
        print("\n👋 正在关闭服务器...")
        stop_generator()
        danmaku_scheduler.stop()
        print("服务器已关闭")