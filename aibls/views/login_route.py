import asyncio
import logging
import os
import shutil
from typing import Any

from bilibili_api import Credential
from bilibili_api.login_v2 import QrCodeLogin, QrCodeLoginEvents
from flask import jsonify, session, render_template

from aibls.services.user_service_file import UserServiceFile
from aibls.utils.snowflake import Snowflake
from aibls.views import user_api

logger = logging.getLogger(__name__)

user_service = UserServiceFile()

qrcode_login = QrCodeLogin()

def to_sync(awaitable):
    """异步转同步的辅助函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(awaitable)


@user_api.route('/login/page')
def login_page():
    """主页"""
    return render_template('login.html')

@user_api.route("/login/qrcode")
def refresh_qrcode():
    """
    刷新登录二维码
    :return:
    """
    #清除存量数据
    logger.info("生成二维码的保存目录")
    _clear_qrcode_file()

    qrcode_key = Snowflake().next_id()
    #获取二维码的元数据（从login中获取方法）
    logger.info("生成二维码的KEY={}".format(qrcode_key))
    to_sync(qrcode_login.generate_qrcode())
    source_url = qrcode_login.get_qrcode_picture().url
    #创建二维码，并获取文件名（不包括路径）
    img_url = _copy_qrcode_local(source_url,qrcode_key)

    logger.info("生成二维码的IMAGEURL={}".format(img_url))

    session["qrcode_key"] = qrcode_key
    session.modified = True
    logger.info("生成二维码后，保存到Session中的KEY={}".format(session.get("qrcode_key")))
    return jsonify({"code": 0, "img_url": img_url})


def _copy_qrcode_local(qrcode_url,qrcode_key):
    #应用根目录
    rt_path = os.getcwd()
    #目标目录
    dir_path = f'{rt_path}\\web\\static\\images\\qrcodes'
    logger.info("生成二维码的保存目录={}".format(dir_path))
    #如果目录不存在，则生成目录
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    #定义文件名
    filename = f"qrcode_{qrcode_key}.png"
    file_path = dir_path + "\\" + filename
    #将临时目录的文件Copy到对应目录
    shutil.copyfile(qrcode_url.replace("file://",""), file_path)
    #返回目标二维码图片的WebUrl
    img_url = f'/static/images/qrcodes/{filename}'
    return img_url

@user_api.route("/login/poll")
def poll_status():
    ot_resp = {"code": 0, "text": "成功"}
    try:
        qrcode_key = session.get("qrcode_key")
        logger.info("校验扫码状态的KEY={}".format(qrcode_key))
        if qrcode_key is None:
            ot_resp = {"code": 1, "text": "需要重新生成二维码！"}
        else:
            poll_data : QrCodeLoginEvents = to_sync(qrcode_login.check_state())
            result = _do_qrcode_event(poll_data)
            if result is None:
                ot_resp = {"code": 1, "text": "正在等待"}
            elif result["code"] == 0:
                credential: Credential = qrcode_login.get_credential()
                #保存数据
                login_user:dict[str,Any] = user_service.save_login_user(credential)

                #登录用户进Session
                session["login_user"] = login_user

                #清除数据
                _clear_qrcode_file()

                ot_resp = {"code": 0, "text": "成功"}
            else:
                ot_resp = result
    except Exception as e:
        logger.error("发生异常-刷新二维码时:%s" % (str(e)))
        ot_resp = {"code": 1102, "text": str(e)}
    finally:
        return jsonify(ot_resp)

def _clear_qrcode_file():
    """
    清除Session中的二维码图像文件和KEY
    :return:
    """
    #
    if 'qrcode_key' in session:
        qrcode_key = session.get("qrcode_key")
        #组装文件路径
        rt_path = os.getcwd()
        file_path = f'{rt_path}\\web\\static\\images\\qrcodes\\qrcode_{qrcode_key}.png'
        logger.info("清除二维码文件={}".format(file_path))
        #删除文件
        if os.path.exists(file_path):
            os.remove(file_path)
        #清除Session
        del session["qrcode_key"]

def _do_qrcode_event(event):
    """
    执行扫码状态检查和何处
    :param qrcode_key:
    :return:
    """
    if event == QrCodeLoginEvents.SCAN:
        return {"code": 86101, "text": "请扫码二维码"}
    elif event == QrCodeLoginEvents.CONF:
        return {"code": 86090, "text": "点下确认啊"}
    elif event == QrCodeLoginEvents.TIMEOUT:
        return {"code": 86038, "text": "二维码过期，请扫新二维码"}
    elif event == QrCodeLoginEvents.DONE:
        return {"code": 0, "text": "成功"}

    else:
        return None