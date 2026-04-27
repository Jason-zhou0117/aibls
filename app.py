# 首先执行 eventlet.monkey_patch()
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

from aibls import db, config
from aibls.decorators.decorator import check_session_go_login_decorator


from aibls.views.room_route import room_service
from aibls.views.live_route import danmu_service, generator

from stock_io import socketio, message_queue


def create_app():
    app = Flask(__name__,static_folder='web/static',     # 静态文件目录
            template_folder='web/templates')
    #Session的配置
    app.config.from_object(config)
    app.debug = True
    rt_path = app.root_path
    app.config['SESSION_FILE_DIR'] = f'{rt_path}/sessions'  # session保存路径

    #注册蓝图
    register_blueprint(app)
    #注册配置日志
    register_log(app)
    #注册使用Session
    Session(app)
    # 初始化数据库管理器
    db.init_app(app)

    return app

def register_blueprint(app: Flask):
    from aibls.views import user_api, room_api, live_api
    """
    这是注册
    :param app: 传入Flask APP
    :return:
    """
    #注册用户登录API的蓝图
    app.register_blueprint(user_api)
    #注册房间API的蓝图
    app.register_blueprint(room_api)
    #注册弹幕API的蓝图
    app.register_blueprint(live_api)

    print_registered_routes(app)

def print_registered_routes(app):
    """调试函数：启动时打印所有路由"""
    print("\n" + "=" * 60)
    print("当前已成功注册的路由列表：")
    print("=" * 60)
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"{rule.endpoint:30s} | {methods:15s} | {rule.rule}")
    print("=" * 60 + "\n")

def register_log(app: Flask):
    """
    这是注册日志信息
    :param app: 传入Flask APP
    :return:
    """
    rt_path = app.root_path
    app.logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    str_day = time.strftime("%Y-%m-%d", time.localtime())
    file_handler = RotatingFileHandler( f'{rt_path}/logs/log-{str_day}.log',maxBytes=10 * 1024 * 1024, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)


#初始化APP
app= create_app()
socketio.init_app(app,
                    cors_allowed_origins="*",
                    async_mode='gevent',
                    logger=True,
                    engineio_logger=True)


@app.route("/index")
@check_session_go_login_decorator
def index():
    login_user : dict[str,Any] = session.get("login_user")
    result_data = room_service.load_rooms_by_filter(None)
    return render_template('index.html',nick_name=login_user["nick_name"],
                           user_face=login_user["user_face"],
                           rooms=result_data["items"])

@app.route('/proxy/image')
def proxy_image():
    """
    代理外部图片
    使用示例: /proxy/image?url=https://example.com/image.jpg
    """
    try:
        image_url = request.args.get('url')
        if not image_url:
            return "缺少图片URL参数", 400
        logging.info("图片地址：image_url={}".format(image_url))
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }

        # 请求图片
        response = requests.get(image_url, headers=headers, timeout=10)

        # 检查响应
        if response.status_code != 200:
            return f"获取图片失败: {response.status_code}", 404

        logging.info("图片地址：响应={}".format(response))
        # 返回图片
        return Response(
            response.content,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )

    except Exception as e:
        logging.error(f"代理图片失败: {str(e)}")
        return f"代理图片失败: {str(e)}", 500

# 添加调试路由 - 查看所有路由
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




if __name__ == "__main__":
    try:
        print("=" * 60)
        print("启动服务器...")
        print(f"生成器ID: {generator.generator_id}")
        print(f"队列大小: {message_queue.qsize()}")
        print("=" * 60)
        print("访问地址: http://localhost:5000")
        print("=" * 60)

        # 使用 socketio.run 而不是 app.run
        socketio.run(app,
                     debug=True,
                     port=5000,
                     allow_unsafe_werkzeug=True,
                     use_reloader=False)  # 禁用重载器以避免线程问题

    except KeyboardInterrupt:
        print("\n👋 正在关闭服务器...")
        generator.stop()
        print("服务器已关闭")
