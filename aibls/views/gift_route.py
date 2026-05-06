import asyncio

from bilibili_api import Credential

import os
import uuid
import logging
from datetime import datetime

from flask import request, jsonify, session, render_template
from werkzeug.utils import secure_filename

from aibls import LoginCookie
from aibls.decorators import check_session_2api_decorator, check_session_go_login_decorator
from aibls.services import gift_service, bili_live_service, room_service
from aibls.settings import VIDEO_DIR
from aibls.views import gift_api

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'mp4', 'webm', 'avi', 'mov', 'mkv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_login_credential() -> Credential:
    """获取当前登录用户的凭证"""
    login_user = session.get("login_user")
    return LoginCookie.dic_to_credential(login_user)

# ==================== 路由 ====================
@gift_api.route('/api/gift/refresh')
@check_session_2api_decorator
def refresh_gift_route():
    room_data = room_service.get_default_room()
    logger.info(f'获取默认房间信息{room_data}')
    room_id = room_data.get('id')
    gif_common: dict = asyncio.run(bili_live_service.get_gif_config(room_id))

    gift_service.sync_from_bili(gif_common)

    return jsonify({
        "code": 0,
        "message": "查询成功"
    })


# ==================== 页面 ====================

@gift_api.route('/gift_config')
@check_session_go_login_decorator
def gift_config_page():
    """礼物特效配置页面"""
    login_user = session.get("login_user", {})
    return render_template('gift_config.html',
                           nick_name=login_user.get("nick_name", "未登录"),
                           user_face=login_user.get("user_face", ""))


# ==================== 礼物管理 API ====================

@gift_api.route('/api/gifts/active', methods=['GET'])
@check_session_2api_decorator
def get_active_gifts():
    """获取上架礼物列表"""
    gifts = gift_service.get_active_gifts()
    return jsonify({'code': 0, 'data': gifts})


@gift_api.route('/api/gifts/inactive', methods=['GET'])
@check_session_2api_decorator
def get_inactive_gifts():
    """获取下架礼物列表"""
    gifts = gift_service.get_inactive_gifts()
    return jsonify({'code': 0, 'data': gifts})


@gift_api.route('/api/gifts/<int:gift_id>/move_to_active', methods=['POST'])
@check_session_2api_decorator
def move_to_active(gift_id):
    """移动到上架列表"""
    success, message = gift_service.move_gift_to_active(gift_id)
    if not success:
        return jsonify({'code': -1, 'message': message})
    return jsonify({'code': 0, 'message': message})


@gift_api.route('/api/gifts/<int:gift_id>/move_to_inactive', methods=['POST'])
@check_session_2api_decorator
def move_to_inactive(gift_id):
    """移动到下架列表"""
    success, message = gift_service.move_gift_to_inactive(gift_id)
    if not success:
        return jsonify({'code': -1, 'message': message})
    return jsonify({'code': 0, 'message': message})

@gift_api.route('/api/gifts', methods=['GET'])
@check_session_2api_decorator
def get_gifts():
    """获取礼物列表"""
    gifts = gift_service.get_all_gifts()
    return jsonify({'code': 0, 'data': gifts})


@gift_api.route('/api/gifts/<int:gift_id>', methods=['GET'])
@check_session_2api_decorator
def get_gift_detail(gift_id):
    """获取礼物详情"""
    gift = gift_service.get_gift_by_id(gift_id)
    if not gift:
        return jsonify({'code': -1, 'message': '礼物不存在'})
    return jsonify({'code': 0, 'data': gift.to_dict()})


@gift_api.route('/api/gifts', methods=['POST'])
@check_session_2api_decorator
def add_gift():
    """添加礼物"""
    data = request.get_json()

    if not data.get('gift_id'):
        return jsonify({'code': -1, 'message': '礼物ID不能为空'})
    if not data.get('gift_name'):
        return jsonify({'code': -1, 'message': '礼物名称不能为空'})

    gift, error = gift_service.add_gift(data)
    if error:
        return jsonify({'code': -1, 'message': error})

    return jsonify({'code': 0, 'data': gift, 'message': '添加成功'})


@gift_api.route('/api/gifts/<int:gift_id>', methods=['PUT'])
@check_session_2api_decorator
def update_gift(gift_id):
    """更新礼物信息"""
    data = request.get_json()
    gift, error = gift_service.update_gift(gift_id, data)
    if error:
        return jsonify({'code': -1, 'message': error})

    return jsonify({'code': 0, 'data': gift, 'message': '更新成功'})


@gift_api.route('/api/gifts/<int:gift_id>', methods=['DELETE'])
@check_session_2api_decorator
def delete_gift(gift_id):
    """删除礼物"""
    success, message = gift_service.delete_gift(gift_id)
    if not success:
        return jsonify({'code': -1, 'message': message})

    return jsonify({'code': 0, 'message': message})


# ==================== 特效视频管理 API ====================

@gift_api.route('/api/gifts/<int:gift_id>/videos', methods=['GET'])
@check_session_2api_decorator
def get_gift_videos(gift_id):
    """获取礼物的特效视频列表"""
    videos, error = gift_service.get_gift_videos(gift_id)
    if error:
        return jsonify({'code': -1, 'message': error})

    return jsonify({'code': 0, 'data': videos})


@gift_api.route('/api/gift/videos', methods=['POST'])
@check_session_2api_decorator
def add_video():
    """添加特效视频"""
    data = request.get_json()
    gift_id = data.get('gift_id')
    video_id = data.get('video_id')
    title = data.get('title')
    url = data.get('url')
    path = data.get('path')

    if not gift_id:
        return jsonify({'code': -1, 'message': '礼物ID不能为空'})
    if not title:
        return jsonify({'code': -1, 'message': '视频名称不能为空'})

    video, error = gift_service.add_video(gift_id, video_id or str(uuid.uuid4())[:8], title, url, path)
    if error:
        return jsonify({'code': -1, 'message': error})

    return jsonify({'code': 0, 'data': video, 'message': '添加成功'})


@gift_api.route('/api/gift/videos/<video_uuid>', methods=['DELETE'])
@check_session_2api_decorator
def delete_video(video_uuid):
    """删除特效视频"""
    success, message = gift_service.delete_video(video_uuid)
    if not success:
        return jsonify({'code': -1, 'message': message})

    return jsonify({'code': 0, 'message': message})


# ==================== 视频文件上传 ====================

@gift_api.route('/api/upload/gift_video', methods=['POST'])
@check_session_2api_decorator
def upload_gift_video():
    """上传礼物特效视频"""
    if 'video' not in request.files:
        return jsonify({'code': -1, 'message': '没有选择文件'})

    file = request.files['video']
    if file.filename == '':
        return jsonify({'code': -1, 'message': '文件名为空'})

    if not allowed_file(file.filename):
        return jsonify({'code': -1, 'message': '不支持的文件格式'})

    original_name = secure_filename(file.filename)
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    # new_filename = f"gift_{uuid.uuid4().hex[:12]}.{file_ext}"

    # 确保目录存在
    os.makedirs(VIDEO_DIR, exist_ok=True)
    save_path = os.path.join(VIDEO_DIR, file.filename)
    if not os.path.exists(save_path):
        file.save(save_path)

    video_url = f"/static/videos/{file.filename}"
    title = original_name.rsplit('.', 1)[0]

    return jsonify({
        'code': 0,
        'data': {
            'filename': original_name,
            'title': title,
            'url': video_url,
            'path': save_path,
            'size': os.path.getsize(save_path)
        },
        'message': '上传成功'
    })


# ==================== 测试播放 ====================

@gift_api.route('/api/gift/video/test_play', methods=['POST'])
@check_session_2api_decorator
def test_play_video():
    """测试播放礼物特效视频"""
    from aibls.stock_io import socketio

    data = request.get_json()
    gift_id = data.get('gift_id')
    video_id = data.get('video_id')

    video = None
    if video_id:
        from aibls.models.database import GiftVideo
        video = GiftVideo.query.filter_by(id=video_id).first()

    if not video and gift_id:
        gift = gift_service.get_gift_by_id(gift_id)
        if gift and gift.videos.count() > 0:
            video = gift.videos.first()

    if not video:
        return jsonify({'code': -1, 'message': '没有找到可播放的视频'})

    test_command = {
        'type': 'video_command',
        'action': 'play_video',
        'video_url': video.url,
        'video_path': video.path,
        'video_name': video.title,
        'gift_id': gift_id,
        'is_test': True,
        'timestamp': datetime.now().isoformat()
    }

    socketio.emit('video_command', test_command)

    return jsonify({
        'code': 0,
        'message': f'正在播放: {video.title}',
        'data': test_command
    })
