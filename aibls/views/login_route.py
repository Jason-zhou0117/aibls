# aibls/views/login_route.py
import asyncio
import logging
import os

from bilibili_api import Credential
from bilibili_api.login_v2 import QrCodeLogin, QrCodeLoginEvents
from flask import jsonify, session, render_template, current_app

from aibls.services import user_service_file
from aibls.utils import Snowflake
from aibls.views import user_api
from aibls.settings import STATIC_DIR, APP_ROOT


qrcode_login = QrCodeLogin()

def to_sync(awaitable):
    """异步转同步的辅助函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(awaitable)


def _get_qrcode_dir() -> str:
    """获取二维码保存目录"""
    qrcode_dir = os.path.join(STATIC_DIR, 'images', 'qrcodes')
    os.makedirs(qrcode_dir, exist_ok=True)
    return qrcode_dir


def _get_qrcode_path(qrcode_key: int) -> str:
    """获取二维码文件路径"""
    qrcode_dir = _get_qrcode_dir()
    return os.path.join(qrcode_dir, f'qrcode_{qrcode_key}.png')


def _clear_qrcode_file(qrcode_key: int = None):
    logger = current_app.logger
    """清除二维码文件"""
    if qrcode_key is None:
        qrcode_key = session.pop('qrcode_key', None)

    if qrcode_key:
        file_path = _get_qrcode_path(qrcode_key)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"清除二维码文件: {file_path}")


def _copy_qrcode_local(qrcode_url: str, qrcode_key: int) -> str:
    """复制二维码到本地静态目录"""
    # 复制文件
    src_path = qrcode_url.replace("file://", "")
    dst_path = _get_qrcode_path(qrcode_key)

    import shutil
    shutil.copyfile(src_path, dst_path)

    # 返回 Web 访问 URL
    return f'/static/images/qrcodes/qrcode_{qrcode_key}.png'


def _do_qrcode_event(event) -> dict | None:
    """处理二维码扫码事件"""
    event_map = {
        QrCodeLoginEvents.SCAN: {"code": 86101, "text": "️️️⚠️请扫码二维码"},
        QrCodeLoginEvents.CONF: {"code": 86090, "text": "⚠️点下确认啊"},
        QrCodeLoginEvents.TIMEOUT: {"code": 86038, "text": "❌二维码过期，请扫新二维码"},
        QrCodeLoginEvents.DONE: {"code": 0, "text": "✅成功"},
    }
    return event_map.get(event)


# ==================== 路由 ====================

@user_api.route('/login/page')
def login_page():
    logger = current_app.logger
    """登录页面"""
    login_user = session.get("login_user", {})
    logger.info(f"登录页面的登录用户：{login_user}")
    return render_template('login.html',
                           nick_name=login_user.get("nick_name", "未登录"),
                           user_face=login_user.get("user_face", ""))


@user_api.route("/login/qrcode")
def refresh_qrcode():
    logger = current_app.logger

    """刷新登录二维码"""
    logger.info("开始生成登录二维码")

    # 清除旧数据
    _clear_qrcode_file()

    # 生成新二维码
    qrcode_key = Snowflake().next_id()
    to_sync(qrcode_login.generate_qrcode())
    source_url = qrcode_login.get_qrcode_picture().url

    # 保存到本地
    img_url = _copy_qrcode_local(source_url, qrcode_key)

    # 保存到 Session
    session["qrcode_key"] = qrcode_key
    session.modified = True

    logger.info(f"二维码生成成功, KEY={qrcode_key}, URL={img_url}")

    return jsonify({"code": 0, "img_url": img_url})


@user_api.route("/login/poll")
def poll_status():
    """轮询扫码状态"""

    logger = current_app.logger
    try:
        qrcode_key = session.get("qrcode_key")
        logger.info(f"校验扫码状态, KEY={qrcode_key}")

        if qrcode_key is None:
            return jsonify({"code": 1, "text": "需要重新生成二维码！"})

        poll_data = to_sync(qrcode_login.check_state())
        result = _do_qrcode_event(poll_data)

        if result is None:
            return jsonify({"code": 1, "text": "正在等待"})

        if result["code"] == 0:
            credential :Credential = qrcode_login.get_credential()
            login_user = user_service_file.save_login_user(credential)
            session["login_user"] = login_user
            _clear_qrcode_file(qrcode_key)
            return jsonify({"code": 0, "text": "成功"})

        return jsonify(result)

    except Exception as e:
        logger.error(f"轮询扫码状态异常: {e}")
        return jsonify({"code": 1102, "text": str(e)})