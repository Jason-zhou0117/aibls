# aibls/views/vip_config_route.py
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from bilibili_api import Credential
from flask import request, jsonify, session, render_template
from werkzeug.utils import secure_filename

from aibls import LoginCookie
from aibls.decorators import check_session_2api_decorator, check_session_go_login_decorator
from aibls.models import db
from aibls.services import vip_service,bili_user_service
from aibls.utils import VIPConfig
from aibls.views import  vip_api

logger = logging.getLogger(__name__)

# 上传配置
UPLOAD_FOLDER = Path(__file__).parent.parent.parent / 'web' / 'static' / 'videos'
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'avi', 'mov', 'mkv'}

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== VIP用户管理 API ====================

@vip_api.route('/api/vip/users', methods=['GET'])
@check_session_2api_decorator
def get_vip_users():
    """获取VIP用户列表"""
    users = vip_service.get_all_users()
    return jsonify({'code': 0, 'data': users})


@vip_api.route('/api/vip/users', methods=['POST'])
@check_session_2api_decorator
def add_vip_user():
    """添加VIP用户"""
    data = request.get_json()
    uid = str(data.get('uid'))
    if not uid:
        return jsonify({'code': -1, 'message': 'UID不能为空'})



    try:
        # 准备当前登录用户
        login_user: dict[str, Any] = session.get("login_user")
        user_credential: Credential = LoginCookie.dic_to_credential(login_user)
        # 获取Bili用户信息
        bili_user = bili_user_service.get_user_info(uid,user_credential)

        if bili_user is None:
            return jsonify({'code': -2, 'message': 'B站查询该用户信息失败，请确认UID是否正确'})

        name = bili_user.get("name","")
        face = bili_user.get("face","")


        user, error = vip_service.add_user(uid, name, name,face)
        if error:
            return jsonify({'code': -1, 'message': error})

        return jsonify({'code': 0, 'data': user, 'message': '添加成功'})
    except Exception as e:
        return jsonify({'code': -2, 'message': '保存用户信息失败'})


@vip_api.route('/api/vip/users/<uid>', methods=['PUT'])
@check_session_2api_decorator
def update_vip_user(uid):
    """更新VIP用户信息"""
    data = request.get_json()
    user, error = vip_service.update_user(
        uid,
        name=data.get('name'),
        nickname=data.get('nickname'),
        face=data.get('face')
    )
    if error:
        return jsonify({'code': -1, 'message': error})

    return jsonify({'code': 0, 'data': user, 'message': '更新成功'})


@vip_api.route('/api/vip/users/<uid>', methods=['DELETE'])
@check_session_2api_decorator
def delete_vip_user(uid):
    """删除VIP用户"""
    success, message = vip_service.delete_user(uid)
    if not success:
        return jsonify({'code': -1, 'message': message})

    return jsonify({'code': 0, 'message': message})


@vip_api.route('/api/vip/users/<uid>', methods=['GET'])
@check_session_2api_decorator
def get_vip_user_detail(uid):
    """获取单个VIP用户详情"""
    user = vip_service.get_user_by_uid(uid)
    if not user:
        return jsonify({'code': -1, 'message': '用户不存在'})

    return jsonify({'code': 0, 'data': user.to_dict()})


# ==================== 入场视频管理 API ====================

@vip_api.route('/api/vip/users/<uid>/videos', methods=['GET'])
@check_session_2api_decorator
def get_user_videos(uid):
    """获取指定用户的入场视频列表"""
    videos, error = vip_service.get_user_videos(uid)
    if error:
        return jsonify({'code': -1, 'message': error})

    return jsonify({'code': 0, 'data': videos})


@vip_api.route('/api/vip/videos', methods=['POST'])
@check_session_2api_decorator
def add_video():
    """添加入场视频"""
    data = request.get_json()
    uid = str(data.get('uid'))
    video_id = str(uuid.uuid4())[:8]
    video_title = data.get('video_name')
    video_url = data.get('video_url')
    video_path = data.get('video_path')

    if not uid or not video_title:
        return jsonify({'code': -1, 'message': '参数不完整'})

    video, error = vip_service.add_video(uid, video_id,video_title, video_url, video_path)
    if error:
        return jsonify({'code': -1, 'message': error})

    return jsonify({'code': 0, 'data': video, 'message': '添加成功'})


@vip_api.route('/api/vip/videos/<video_id_key>', methods=['DELETE'])
@check_session_2api_decorator
def delete_video(video_id_key):
    """删除入场视频"""
    success, message = vip_service.delete_video(video_id_key)
    if not success:
        return jsonify({'code': -1, 'message': message})

    return jsonify({'code': 0, 'message': message})


# ==================== 视频文件上传 API ====================

@vip_api.route('/api/upload/video', methods=['POST'])
@check_session_2api_decorator
def upload_video():
    """上传视频文件"""
    if 'video' not in request.files:
        return jsonify({'code': -1, 'message': '没有选择文件'})

    file = request.files['video']

    if file.filename == '':
        return jsonify({'code': -1, 'message': '文件名为空'})

    if not allowed_file(file.filename):
        return jsonify({'code': -1, 'message': '不支持的文件格式，请上传 mp4/webm/avi/mov/mkv'})
    logger.info(f"上传视频文件得文件名为={file.filename}")
    # 生成安全的文件名
    original_name = secure_filename(file.filename)
    logger.info(f"上传视频文件得文件名为={original_name}")
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex[:12]}.{file_ext}"
    save_path = VIPConfig.get_video_path(new_filename)

    file.save(str(save_path))

    # 生成访问URL
    video_url = f"/static/videos/{new_filename}"

    return jsonify({
        'code': 0,
        'data': {
            'filename': original_name,
            'title': original_name.rsplit('.', 1)[0],  # 去掉扩展名作为标题
            'url': video_url,
            'path': str(save_path),
            'size': os.path.getsize(save_path)
        },
        'message': '上传成功'
    })


@vip_api.route('/vip_config')
@check_session_go_login_decorator
def vip_config_page():
    """VIP配置页面"""
    login_user = session.get("login_user", {})
    return render_template('vip_config.html',
                          nick_name=login_user.get("nick_name", "未登录"),
                          user_face=login_user.get("user_face", ""))


@vip_api.route('/api/video/test_play', methods=['POST'])
@check_session_2api_decorator
def test_play_video():
    """测试播放视频（不触发入场，直接发送播放指令）"""
    from aibls.stock_io import socketio

    data = request.get_json()
    video_id_key = data.get('id_key')

    logger.info(f'测试时的={video_id_key}')

    video = vip_service.get_video_by_id(video_id_key)
    if not video:
        return jsonify({'code': -1, 'message': '视频ID不正确'})

    video_dic = video.to_dict()
    video_url = video_dic.get('url')
    video_name = video_dic.get('title', '测试视频')
    video_path = video_dic.get('path', '')

    if not video_url:
        return jsonify({'code': -1, 'message': '缺少视频URL参数'})

    # 构建测试播放指令
    test_command = {
        'type': 'video_command',
        'action': 'play_video',
        'video_url': video_url,
        'video_name': video_name,
        'video_path': video_path,
        'is_test': True,  # 标记为测试消息
        'timestamp': datetime.now().isoformat()
    }

    # 通过 SocketIO 推送到视频播放器
    socketio.emit('video_command', test_command)

    logger.info(f"测试播放视频: {video_name} ({video_url}),path: {video_path}")

    return jsonify({
        'code': 0,
        'message': f'正在播放: {video_name}',
        'data': test_command
    })
