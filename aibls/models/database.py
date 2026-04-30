# aibls/models/database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class VIPUser(db.Model):
    """VIP用户表"""
    __tablename__ = 'vip_users'

    userid = db.Column(db.String(50), primary_key=True, nullable=False, index=True)  # B站UID
    name = db.Column(db.String(100), nullable=False)  # 用户名
    nickname = db.Column(db.String(100))  # 昵称/别名
    face = db.Column(db.String(500))  # 头像URL
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联视频
    videos = db.relationship('UserVideo', backref='vip_user', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'userid': self.userid,
            'name': self.name,
            'nickname': self.nickname or self.name,
            'face': self.face,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'videos': [v.to_dict() for v in self.videos]
        }

    def to_list_dict(self):
        """转换为列表格式（不含视频详情）"""
        return {
            'userid': self.userid,
            'name': self.name,
            'nickname': self.nickname or self.name,
            'face': self.face,
            'video_count': self.videos.count()
        }


class UserVideo(db.Model):
    """入场视频表"""
    __tablename__ = 'user_video'
    id = db.Column(db.String(50), primary_key=True, nullable=False)
    video_id = db.Column(db.String(50),nullable=False)
    userid = db.Column(db.String(50), db.ForeignKey('vip_users.userid', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)  # 视频名称
    url = db.Column(db.String(500), nullable=False)  # 访问URL
    path = db.Column(db.String(500), nullable=False)  # 物理路径
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'url': self.url,
            'path': self.path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VideoInfo(db.Model):
    """入场视频表"""
    __tablename__ = 'videos'

    video_id = db.Column(db.String(50),primary_key=True, nullable=False)  # UUID
    title = db.Column(db.String(200), nullable=False)  # 视频名称
    url = db.Column(db.String(500), nullable=False)  # 访问URL
    path = db.Column(db.String(500), nullable=False)  # 物理路径
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'url': self.url,
            'path': self.path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }