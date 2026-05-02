import asyncio
import functools

from bilibili_api import Credential
from flask import session, render_template, jsonify

from aibls.exceptions.BLSException import BLSException
from aibls.models.users import LoginCookie
from aibls.services import bili_user_service

def check_session_go_login_decorator(func):
    """校验是否登录，如没有跳转到登录页面"""
    @functools.wraps(func)
    def inner(*args, **kwargs):
        login_user = session.get("login_user")
        if login_user is None:
            return render_template('login.html')
        else:
            try:
                #重新获取一次登录用户信息，以免登录态过期
                user_credential:Credential = LoginCookie.dic_to_credential(login_user)
                login_user_info = bili_user_service.test_login_status(user_credential)
                if login_user_info:
                    session["login_user"] = login_user
                    return func(*args,**kwargs)
                else:
                    return render_template('login.html')
            except BLSException as e:
                return render_template('login.html')
    return inner

def check_session_2api_decorator(func):
    """在接口调用时，校验是否登录，如没有则返回错误消息"""
    @functools.wraps(func)
    def inner(*args,**kwargs):
        login_user = session.get("login_user")
        if login_user is None:
            return jsonify({"code":-10000,"message":"用户未登录或Session失效"})
        else:
            return func(*args,**kwargs)
    return inner
