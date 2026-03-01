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
from aibls.views import user_api, room_api, live_api

from aibls.views.room_route import room_service
from aibls.views.live_route import danmu_service
from aibls.views.login_route import user_service
from stock_io import socketio


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
socketio.init_app(app, cors_allowed_origins="*",async_mode='eventlet'  )


@app.route("/")
@check_session_go_login_decorator
def index():
    login_user : dict[str,Any] = session.get("login_user")
    filters = {"login_id": login_user["login_id"]}
    result_data = room_service.load_rooms_by_filter(filters)
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
#执行APP
if __name__ == "__main__":
    socketio.run(app, debug=True,port=5000, allow_unsafe_werkzeug=True if app.debug else False)
