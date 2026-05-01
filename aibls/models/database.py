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


class GiftInfo(db.Model):
    """礼物信息表"""
    __tablename__ = 'gift_info'

    gift_id = db.Column(db.Integer, primary_key=True, nullable=False)  # 礼物编号
    gift_name = db.Column(db.String(200), nullable=False)
    gift_icon = db.Column(db.String(500), nullable=False)
    price_origin = db.Column(db.NUMERIC(10, 2), nullable=False)
    price_gold = db.Column(db.NUMERIC(10, 2), nullable=False)
    price_cny = db.Column(db.NUMERIC(10, 2), nullable=False)
    is_blind_box = db.Column(db.String(1), nullable=False)
    blind_box_id = db.Column(db.Integer, nullable=False)
    has_video = db.Column(db.String(1), nullable=False)
    is_active = db.Column(db.String(1), nullable=False, default='1')  # 新增：是否上架 '1'=上架，'0'=下架
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联视频
    videos = db.relationship('GiftVideo', backref='gift_info', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'gift_id': self.gift_id,
            'gift_name': self.gift_name,
            'gift_icon': self.gift_icon,
            'price_origin': float(self.price_origin) if self.price_origin else 0,
            'price_gold': float(self.price_gold) if self.price_gold else 0,
            'price_cny': float(self.price_cny) if self.price_cny else 0,
            'is_blind_box': self.is_blind_box,
            'blind_box_id': self.blind_box_id,
            'has_video': self.has_video,
            'is_active': self.is_active,  # 新增
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'video_count': self.videos.count()
        }

    def to_list_dict(self):
        """列表用（简化）"""
        return {
            'gift_id': self.gift_id,
            'gift_name': self.gift_name,
            'gift_icon': self.gift_icon,
            'price_cny': float(self.price_cny) if self.price_cny else 0,
            'has_video': self.has_video,
            'is_active': self.is_active,  # 新增
            'video_count': self.videos.count()
        }


class GiftVideo(db.Model):
    """礼物特效视频表"""
    __tablename__ = 'gift_video'

    id = db.Column(db.String(50), primary_key=True, nullable=False)
    video_id = db.Column(db.String(50), nullable=False)
    gift_id = db.Column(db.Integer, db.ForeignKey('gift_info.gift_id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'gift_id': self.gift_id,
            'title': self.title,
            'url': self.url,
            'path': self.path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }