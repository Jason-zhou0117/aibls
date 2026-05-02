# aibls/services/vip_service.py
import os
import uuid
from datetime import datetime

from bilibili_api import Credential
from flask import current_app

from aibls.models.database import db, VIPUser, UserVideo
from aibls.services import bili_user_service

class VIPService:
    """VIP用户服务类"""

    @staticmethod
    def get_all_users():
        """获取所有VIP用户（列表格式）"""
        users = VIPUser.query.all()
        return [u.to_list_dict() for u in users]

    @staticmethod
    def get_user_by_uid(uid):
        """根据UID获取用户"""
        return VIPUser.query.filter_by(userid=str(uid)).first()

    @staticmethod
    def add_user(uid, name, nickname=None, face=None):
        """添加VIP用户"""
        # 检查是否已存在
        existing = VIPUser.query.filter_by(userid=str(uid)).first()
        if existing:
            return None, "用户已存在"

        user = VIPUser(
            userid=str(uid),
            name=name,
            nickname=nickname or name,
            face=face
        )
        db.session.add(user)
        db.session.commit()
        return user.to_dict(), None

    @staticmethod
    def update_user(uid, name=None, nickname=None, face=None):
        """更新VIP用户信息"""
        user = VIPUser.query.filter_by(userid=str(uid)).first()
        if not user:
            return None, "用户不存在"

        if name:
            user.name = name
        if nickname:
            user.nickname = nickname
        if face:
            user.face = face

        user.updated_at = datetime.now()
        db.session.commit()
        return user.to_dict(), None

    @staticmethod
    def delete_user(uid):
        logger = current_app.logger
        """删除VIP用户（级联删除关联视频）"""
        user = VIPUser.query.filter_by(userid=str(uid)).first()
        if not user:
            return False, "用户不存在"

        # 删除关联的视频文件
        for video in user.videos:
            video_path = video.path
            if video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception as e:
                    logger.error(f"删除视频文件失败: {e}")

        db.session.delete(user)
        db.session.commit()
        return True, "删除成功"

    @staticmethod
    def get_user_videos(uid):
        """获取用户的入场视频列表"""
        user = VIPUser.query.filter_by(userid=str(uid)).first()
        if not user:
            return [], "用户不存在"

        return [v.to_dict() for v in user.videos], None

    @staticmethod
    def add_video(uid, video_id,title, url, path):
        """为VIP用户添加入场视频"""
        logger = current_app.logger
        user = VIPUser.query.filter_by(userid=str(uid)).first()
        if not user:
            return None, "用户不存在"
        try:
            video = UserVideo(
                id = f'{str(uuid.uuid4())[:8]}-{str(uid)}',
                video_id=video_id,
                userid=str(uid),
                title=title,
                url=url,
                path=path
            )
            db.session.add(video)
            db.session.commit()
            return video.to_dict(), None
        except Exception as e:
            logger.error(f"添加视频失败: {e}")
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def delete_video(id_key):
        """删除入场视频"""
        logger = current_app.logger
        video = UserVideo.query.filter_by(id=id_key).first()
        if not video:
            return False, "视频不存在"

        # 删除视频文件
        video_path = video.path
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception as e:
                logger.error(f"删除视频文件失败: {e}")

        db.session.delete(video)
        db.session.commit()
        return True, "删除成功"

    @staticmethod
    def get_video_by_id(video_id):
        """根据UID获取用户"""
        return UserVideo.query.get(video_id)

    @staticmethod
    async def sync_from_bili(login_credential:Credential):
        """从B站同步礼物数据（批量）"""
        logger = current_app.logger

        try:
            user_list = VIPUser.query.all()
            logger.info(f'同步的VIP用户數量：{len(user_list)}')
            for u in user_list:
                bili_user = await bili_user_service.get_user_info(u.userid,login_credential)
                u.name = bili_user.get("name")
                u.nickname =  bili_user.get("name")
                u.face =  bili_user.get("face")

                db.session.add(u)

            db.session.commit()
            return True, "同步成功"
        except Exception as e:
            logger.error(f"同步VIP用户失败: {e}")
            db.session.rollback()
            return False, str(e)
# 全局服务实例
vip_service = VIPService()