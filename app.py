# app.py
# -*- coding: utf-8 -*-

import os
import sys
# 将当前目录添加到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
# 先导入 settings（必须在最前面，因为其他模块可能需要）
from settings import APP_ROOT, IS_EMBEDDED, DEBUG_MODE, ensure_directories

# 切换到项目根目录
os.chdir(APP_ROOT)

# 将项目根目录添加到 Python 路径
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# ==================== 导入依赖 ====================

import asyncio
import datetime
import queue
import eventlet
import logging
import time
from logging.handlers import RotatingFileHandler
from typing import Any

import requests
from flask import Flask, request, Response, jsonify
from flask_session import Session
from flask import session, render_template

from aibls import config
from aibls.decorators.decorator import check_session_go_login_decorator
from aibls.views import vip_api
from aibls.views.live_route import generator
from aibls.views.room_route import room_service
from stock_io import socketio, message_queue


# ==================== 创建应用 ====================

def create_app():
    """创建 Flask 应用"""
    from settings import STATIC_DIR, TEMPLATE_DIR, SESSION_DIR

    app = Flask(__name__,
                static_folder=STATIC_DIR,
                template_folder=TEMPLATE_DIR)

    # Session 配置
    app.config.from_object(config)
    app.debug = DEBUG_MODE
    app.config['SESSION_FILE_DIR'] = SESSION_DIR

    # 注册蓝图
    register_blueprint(app)
    register_log(app)
    Session(app)
    # db.init_app(app)

    return app


def register_blueprint(app: Flask):
    from aibls.views import user_api, room_api, live_api

    app.register_blueprint(user_api)
    app.register_blueprint(room_api)
    app.register_blueprint(live_api)
    app.register_blueprint(vip_api)

    print_registered_routes(app)


def print_registered_routes(app):
    print("\n" + "=" * 60)
    print("当前已成功注册的路由列表：")
    print("=" * 60)
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.endpoint:30s} | {methods:15s} | {rule.rule}")
    print("=" * 60 + "\n")


def register_log(app: Flask):
    from settings import LOG_DIR

    app.logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    str_day = time.strftime("%Y-%m-%d", time.localtime())

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f'log-{str_day}.log'),
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)


# ==================== 初始化应用 ====================

app = create_app()
socketio.init_app(app,
                  cors_allowed_origins="*",
                  async_mode='gevent',
                  logger=True,
                  engineio_logger=True)


# ==================== 路由 ====================

@app.route('/proxy/image')
def proxy_image():
    try:
        image_url = request.args.get('url')
        if not image_url:
            return "缺少图片URL参数", 400

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

        response = requests.get(image_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return f"获取图片失败: {response.status_code}", 404

        return Response(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except Exception as e:
        logging.error(f"代理图片失败: {str(e)}")
        return f"代理图片失败: {str(e)}", 500


@app.route('/debug/routes')
def debug_routes():
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
        print("=" * 60)
        print(f"运行环境: {'嵌入式运行' if IS_EMBEDDED else '开发环境'}")
        print(f"项目目录: {APP_ROOT}")
        print(f"启动服务器...")
        print(f"生成器ID: {generator.generator_id}")
        print(f"队列大小: {message_queue.qsize()}")
        print("=" * 60)
        print("访问地址: http://localhost:5001")
        print("=" * 60)

        if DEBUG_MODE:
            # PyCharm 调试模式：单进程，开启调试
            socketio.run(app,
                         debug=True,
                         port=5001,
                         use_reloader=False,  # 关键：关闭重载器
                         log_output=True)
        else:
            # 其他环境
            socketio.run(app,
                         debug=DEBUG_MODE,
                         port=5001,
                         allow_unsafe_werkzeug=True,
                         use_reloader=not IS_EMBEDDED)


    except KeyboardInterrupt:
        print("\n👋 正在关闭服务器...")
        generator.stop()
        print("服务器已关闭")