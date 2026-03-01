import asyncio
import functools

from flask import session, render_template, jsonify


def check_session_go_login_decorator(func):
    """校验是否登录，如没有跳转到登录页面"""
    @functools.wraps(func)
    def inner(*args, **kwargs):
        login_user = session.get("login_user")
        if login_user is None:
            return render_template('login.html')
        else:
            return func(*args, **kwargs)
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
