# aibls/models/database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from sqlalchemy import BigInteger, String, Text

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


class RoomInfo(db.Model):
    """房间信息表"""
    __tablename__ = 'room_info'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    cover_url = db.Column(db.String(500), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_face = db.Column(db.String(500), nullable=False)
    is_default = db.Column(db.String(1), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.id,
            'title': self.title,
            'cover_url': self.cover_url,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name,
            'owner_face': self.owner_face,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def to_list_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'room_id': self.id,
            'cover_url': self.cover_url,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name,
            'owner_face': self.owner_face,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SendGiftDetail(db.Model):
    """礼物投喂明细表"""
    __tablename__ = 'send_gift_detail'

    id = db.Column(db.Integer, primary_key=True, nullable=False) #投喂礼物明细号
    room_id = db.Column(db.Integer, nullable=False) #房间编号
    gift_type = db.Column(db.Integer, nullable=False) #0-99 投喂礼物；#101=103，航海；#200：醒目弹幕，
    send_month = db.Column(db.String(10), nullable=False) #月份 yyyy-mm
    send_date = db.Column(db.String(10), nullable=False) #投喂日期 yyyy-mm-dd
    sender_uid = db.Column(db.Integer, nullable=False) #投喂人ID
    sender_name = db.Column(db.String(50), nullable=False) #投喂人昵称
    sender_face = db.Column(db.String(500), nullable=False) #投喂人头像
    receiver_uid = db.Column(db.Integer, nullable=False) #直播间UP的ID
    receiver_name = db.Column(db.String(50), nullable=False) #直播间UP的昵称
    receiver_face = db.Column(db.String(500), nullable=False) #直播间UP的头像
    gift_id = db.Column(db.Integer, nullable=False) #礼物编号
    gift_name = db.Column(db.String(50), nullable=False) #礼物名称
    gift_num = db.Column(db.Integer, nullable=False) #投喂数量
    gift_price_origin = db.Column(db.NUMERIC(10, 2), nullable=False) #礼物单价
    gift_total_coin = db.Column(db.NUMERIC(10, 2), nullable=False) #投喂礼物价值 数量*单价
    blind_gift_id = db.Column(db.Integer, nullable=False) #盲盒的礼物ID。如果是盲盒爆出的礼物，此字段值＞０，否则为０
    blind_gift_name = db.Column(db.String(50), nullable=False) #盲盒的名称
    blind_gift_price = db.Column(db.NUMERIC(10, 2), nullable=False) #盲盒的单价
    blind_gift_total = db.Column(db.NUMERIC(10, 2), nullable=False) #盲盒的总价值 数量*盲盒的单价
    total_scope = db.Column(db.NUMERIC(10, 2), nullable=False) #爆出礼物的价值与盲盒价值的差额
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'send_month': self.send_month,
            'send_date': self.send_date,
            'sender_uid': self.sender_uid,
            'sender_name': self.sender_name,
            'sender_face': self.sender_face,
            'receiver_uid': self.receiver_uid,
            'receiver_name': self.receiver_name,
            'receiver_face': self.receiver_face,
            'gift_id': self.gift_id,
            'gift_type':self.gift_type,
            'gift_name': self.gift_name,
            'gift_num': self.gift_num,
            'gift_price_origin': self.gift_price_origin,
            'gift_total_coin': self.gift_total_coin,
            'blind_gift_id': self.blind_gift_id,
            'blind_gift_name': self.blind_gift_name,
            'blind_gift_price': self.blind_gift_price,
            'blind_gift_total': self.blind_gift_total,
            'total_scope': self.total_scope,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RoomReceiveGifts(db.Model):
    """房间每月收到的礼物汇总"""
    __tablename__ = 'room_receive_gifts'
    id = db.Column(db.Integer, primary_key=True, nullable=False)  #直播间礼物汇总ID
    room_id = db.Column(db.Integer, nullable=False) #房间号
    send_month = db.Column(db.String(10), nullable=False) #统计的月份 yyyy-mm
    gift_total_num = db.Column(db.Integer, nullable=False) #收到的礼物总数
    gift_total_coin = db.Column(db.NUMERIC(10, 2), nullable=False) #收到的礼物总价值
    blind_gift_num = db.Column(db.NUMERIC(10, 2), nullable=False) #盲盒的总数量
    blind_gift_total = db.Column(db.NUMERIC(10, 2), nullable=False) #盲盒的总投入
    blind_gift_scope = db.Column(db.NUMERIC(10, 2), nullable=False) #盲盒的盈亏
    first_uid = db.Column(db.Integer, nullable=False) #当月投喂礼物价值最高的用户ID
    first_name = db.Column(db.String(50), nullable=False) #当月投喂礼物价值最高的用户昵称
    first_face = db.Column(db.String(500), nullable=False) #当月投喂礼物价值最高的用户头像
    first_gift_total = db.Column(db.NUMERIC(10, 2), nullable=False) #榜首送出的礼物总价值
    blind_first_uid = db.Column(db.Integer, nullable=False) #当月盲盒盈亏最高的用户ID
    blind_first_name = db.Column(db.String(50), nullable=False) #当月盲盒盈亏最高的用户昵称
    blind_first_face = db.Column(db.String(500), nullable=False) #当月盲盒盈亏最高的用户头像
    blind_first_scope = db.Column(db.NUMERIC(10, 2), nullable=False) #盲盒榜首的总盈亏
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'send_month': self.send_month,
            'gift_total_num': self.gift_total_num,
            'gift_total_coin': self.gift_total_coin,
            'blind_gift_total': self.blind_gift_total,
            'blind_gift_scope': self.blind_gift_scope,
            'first_uid': self.first_uid,
            'first_name': self.first_name,
            'first_face': self.first_face,
            'blind_first_uid': self.blind_first_uid,
            'blind_first_name': self.blind_first_name,
            'blind_first_face': self.blind_first_face,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LogOffUser(db.Model):
    """用户 Session 表"""
    __tablename__ = "logoff_users"

    user_id = db.Column(BigInteger, primary_key=True, nullable=False)
    user_name = db.Column(String(100), nullable=True)
    user_face = db.Column(String(500), nullable=True)
    credential = db.Column(Text, nullable=False)
    is_open = db.Column(String(1), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联视频
    logoffs = db.relationship('LogOffRoom', backref='logoff_users', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "userid": self.user_id,
            "name": self.user_name,
            "face": self.user_face,
            "credential": self.user_face,
            "is_open": self.is_open,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class LogOffRoom(db.Model):
    """入场视频表"""
    __tablename__ = 'logoff_rooms'
    id = db.Column(db.String(50), primary_key=True, nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('logoff_users.user_id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)  # 起始时间
    end_time = db.Column(db.Time, nullable=False)  # 结束时间
    room_id = db.Column(db.BigInteger,nullable=False)
    title = db.Column(db.String(200), nullable=False)
    cover_url = db.Column(db.String(500), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_face = db.Column(db.String(500), nullable=False)
    is_open = db.Column(String(1), nullable=True)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'room_id': self.room_id,
            'title': self.title,
            'owner_id': self.owner_id,
            'owner_name': self.owner_name, #房间主播名
            'owner_face': self.owner_face,
            "is_open": self.is_open,
            'cover_url': self.cover_url, #房间标题
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M:%S') if self.end_time else None
        }