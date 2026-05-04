import asyncio

import random
import threading
from datetime import datetime

from bilibili_api import Credential, live, sync, user

from aibls.services.room_service import room_service


class AsyncMessageGenerator:
    """异步消息生成器 - 在单个线程中使用 asyncio.new_event_loop"""

    credential = None
    room_id = None
    app = None
    room_info = None

    def __init__(self, message_queue,app = None):
        self.message_queue = message_queue
        self.loop = None
        self.thread = None
        self.running = False
        self.generator_id = random.randint(1000, 9999)
        self._room = None
        self.app = app

    def connect(self, user_credential: Credential, room_id: int):
        self.credential = user_credential
        self.room_id = room_id
        self.room_info = room_service.get_room_data(room_id)
        self._room = live.LiveDanmaku(room_id, False, self.credential)

    def start(self):
        """启动消息生成器线程"""
        logger = self.app.logger
        # 关键修复：检查线程是否活着，而不是检查 None
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._run_async_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info(f"✅ 新线程已启动")
            return True
        else:
            logger.warning(f"线程还在运行中，无法重新启动")
            return False

    def stop(self):
        """停止消息生成器"""
        self.running = False
        logger = self.app.logger
        # 关键：主动断开B站WebSocket连接
        if self._room:
            try:
                # 尝试获取当前连接并断开
                if hasattr(self._room, '_websocket') and self._room._websocket:
                    sync(self._room._websocket.close())
                # 或者调用断开方法（取决于库版本）
                if hasattr(self._room, 'disconnect'):
                    sync(self._room.disconnect())
                logger.info(f"已断开B站房间 {self.room_id} 的连接")
            except Exception as e:
                logger.warning(f"断开连接时出错: {e}")

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 消息生成器 {self.generator_id} 已停止")

    def _run_async_loop(self):
        """在新线程中运行异步事件循环"""
        logger = self.app.logger
        # 创建新的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # 运行异步生成器
            self.loop.run_until_complete(self._run_listener())
        except Exception as e:
            logger.error(f"异步循环错误: {e}")
        finally:
            self.loop.close()
            logger.info(f"异步事件循环已关闭")

    async def _run_listener(self):
        logger = self.app.logger
        self._room.add_event_listener("DANMU_MSG", self.on_danmaku) #普通弹幕
        self._room.add_event_listener("SEND_GIFT", self.on_gift)  # 赠送礼物
        self._room.add_event_listener("GUARD_BUY", self.on_buy_guard)  # 购买舰长
        self._room.add_event_listener("SUPER_CHAT_MESSAGE", self.on_super_chat)  # 醒目留言
        # self._room.add_event_listener("ENTRY_EFFECT", self.on_user_enter)  # 用户进入直播间
        self._room.add_event_listener("INTERACT_WORD_V2", self.on_user_enter_v2)  # 用户进入直播间
        self._room.add_event_listener("VIDEO_CONNECTION_MSG", self.on_user_video_link)  # 用户进入直播间

        try:
            # 连接并开始监听
            sync(self._room.connect())
        except Exception as e:
            logger.error(f"监听连接出错: {e}")


    async def on_danmaku(self, event):
        """
        弹幕事件回调 (由bilibili-api触发)
        正确的事件数据结构：
        """
        logger = self.app.logger
        try:
            logger.debug(f"文字弹幕，原始数据: {event}")
            # 获取弹幕数据
            info = event['data']['info']

            # 解析用户信息
            user_info = info[2]  # 用户信息数组

            # 解析弹幕内容 - info[1] 是弹幕文本
            msg = info[1]

            # 解析用户ID和昵称
            sender_uid = user_info[0]
            sender_name = user_info[1]
            #获取用户详情
            user_detail = await self.load_user_info(sender_uid)

            # 解析粉丝牌信息 (如果有)
            medal_info = info[3] if len(info) > 3 else []
            medal_name = medal_info[1] if len(medal_info) > 1 else ""
            medal_level = medal_info[0] if len(medal_info) > 0 else 0

            #荣耀等级
            honor_info = info[16] if len(info) > 16 else []
            honor_level = honor_info[0] if len(honor_info) > 0 else 0

            # 解析弹幕时间戳
            timestamp = info[0][4] if len(info[0]) > 4 else 0
            dt_str = await self._parse_datetime_str_(timestamp)

            # 构建标准化弹幕数据
            danmu_data = {
                "type": "danmaku",
                "message": msg,  # 弹幕内容 (info[1])
                "room_id":self.room_id,
                "sender_uid": sender_uid,  # 用户昵称
                "sender_name": sender_name,  # 用户ID
                "sender_face" : user_detail["face"] if user_detail is not None else "",
                "timestamp": timestamp,  # 时间戳
                "send_time":dt_str,
                "medal_name": medal_name,  # 粉丝牌名称
                "medal_level":medal_level,  # 粉丝牌等级
                "honor_level":honor_level
            }

            # 调试输出
            logger.info(f"弹幕-文字: {sender_name}: {msg} [粉丝牌: {medal_name} Lv.{medal_level}]")

            self.message_queue.put(danmu_data)
        except Exception as e:
            logger.error(f"解析弹幕数据出错: {e}")

    async def _parse_datetime_str_(self,timestamp) -> str:
        if timestamp > 10 ** 10:  # 判断是否为毫秒（大于10位数）
            timestamp = timestamp / 1000
        dt = datetime.fromtimestamp(timestamp)
        dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        return dt_str

    async def on_gift(self, event):
        """礼物事件回调"""
        logger = self.app.logger
        try:

            logger.debug(f"************礼物弹幕，原始数据: {event}")

            data = event["data"]["data"]

            #送礼物人信息
            sender_uinfo:dict = data.get("sender_uinfo")
            sender_uid = str(sender_uinfo.get("uid"))
            sender_base:dict = sender_uinfo.get("base")
            sender_name = sender_base.get("name")
            sender_face = sender_base.get("face")
            logger.info(f"************礼物弹幕，送礼人:uid= {sender_uid},昵称={sender_name}")

            #收礼物人信息
            room_id = self.room_id
            receiver_info: dict = data.get("receiver_uinfo")
            receiver_uid = str(receiver_info.get("uid"))
            receiver_base: dict = receiver_info.get("base")
            receiver_name = receiver_base.get("name")
            receiver_face = receiver_base.get("face")
            logger.info(f"************礼物弹幕，收礼人:房间号={room_id},uid= {receiver_uid},昵称={receiver_name}")


            #礼物信息
            gift_id = data.get("giftId")
            gift_name = data.get("giftName")
            gift_type = data.get("giftType")
            gift_num = data.get("num")
            gift_price = data.get("price")
            gift_total_coin = data.get("total_coin")
            logger.info(f"************礼物弹幕，礼物信息:礼物={gift_name}（{gift_id}）,类型= {gift_type},数量={gift_num},单价={gift_price},总数={gift_total_coin}")

            #盲盒相关信息
            blind_gift = data.get("blind_gift")
            #如果是盲盒
            blind_gift_id = 0
            blind_gift_name = ""
            blind_gift_price = 0
            blind_gift_total = 0
            if blind_gift:
                blind_gift_id = blind_gift.get("original_gift_id")
                blind_gift_name = blind_gift.get("original_gift_name")
                blind_gift_price = blind_gift.get("original_gift_price")
                blind_gift_total = gift_num * blind_gift_price
                logger.info(
                    f"************礼物弹幕，礼物信息:盲盒爆出={blind_gift_name}（{blind_gift_id}）,盲盒单价={blind_gift_price},盲盒总数={blind_gift_total}")

            total_scope = gift_total_coin - blind_gift_total

            info = {
                "type": "gift",
                "msg": f"弹幕-礼物: {sender_name} 投喂 {gift_name} x{gift_num}",  # 弹幕内容 (info[1])
                "room_id": room_id,
                "sender_uid": sender_uid,
                "sender_name": sender_name,
                "sender_face" : sender_face,
                "receiver_uid": receiver_uid,
                "receiver_name": receiver_name,
                "receiver_face": receiver_face,
                "gift_id": gift_id,
                "gift_type": gift_type,
                "gift_name": gift_name,
                "gift_num": gift_num,
                "price": gift_price,  # 单价 (金瓜子)
                "total_coin": gift_total_coin,
                "blind_gift_id": blind_gift_id,
                "blind_gift_name": blind_gift_name,
                "blind_gift_price": blind_gift_price,
                "blind_gift_total": blind_gift_total,
                "total_scope": total_scope
            }
            #将弹幕放入消息队列
            self.message_queue.put(info)

            logger.info(f"准备查询礼物视频，礼物编号={gift_id}")
            # 2. 检查是否为VIP用户，发送视频播放指令
            # 在函数内部导入，避免循环导入
            from aibls.services.gift_service import gift_service
            if self.app:
                with self.app.app_context():
                    gift_videos, error = gift_service.get_gift_videos(gift_id)
            else:
                # 如果没传入 app，尝试使用 current_app
                from flask import current_app
                with current_app.app_context():
                    gift_videos, error = gift_service.get_gift_videos(gift_id)

            logger.info(f"查询到礼物 {gift_id}下的视频数为:{len(gift_videos)}")

            if len(gift_videos) > 0:
                video = random.choice(gift_videos)
                video_url = video.get("url", "")
                video_path = video.get("path", "")
                video_title = video.get("title", "")
                logger.info(f"礼物特效: {gift_name} (UID: {gift_id})，触发视频播放: {video.get('url', '')}")

                video_command = {
                    "type": "video_command",  # 特殊类型，用于区分
                    "action": "play_video",
                    "video_url": video_url,  # 已经是Flask静态路径
                    "uid": gift_id,
                    "video_path": video_path,
                    "video_name": video_title,
                    "timestamp": datetime.now().isoformat()
                }
                # 放入消息队列，由消费者推送到前端
                self.message_queue.put(video_command)

            #准备记录礼物信息
            logger.debug(f"准备添加投喂礼物到DB")
            from aibls.services.send_gift_service import send_gift_service
            if self.app:
                with self.app.app_context():
                    result, message = send_gift_service.add_send_gift(info)
            else:
                # 如果没传入 app，尝试使用 current_app
                from flask import current_app
                with current_app.app_context():
                    result, message = send_gift_service.add_send_gift(info)
            logger.debug(f"添加投喂记录结果：{result},{message}")
        except Exception as e:
            logger.error(f"解析礼物数据出错: {e}")

    async def on_buy_guard(self, event):
        """上舰事件回调"""
        logger = self.app.logger
        try:
            logger.debug(f"***********上舰: {event}")
            data = event["data"]["data"]
            # 舰长等级对应: 3=舰长, 2=提督, 1=总督
            guard_level_names = {1: "总督", 2: "提督", 3: "舰长"}
            guard_name = guard_level_names.get(data["guard_level"], "未知")

            info = {
                "type": "guard",
                "msg": f"{data['username']} 开通 {guard_name} x {data['num']} 个月",
                "sender_name": data["username"],
                "sender_uid": data["uid"],
                "guard_level": data["guard_level"],
                "guard_name": guard_name,
                "num": data["num"]
            }
            logger.info(f"上舰: {data['username']} 开通{guard_name}")

            #将弹幕放入消息队列
            self.message_queue.put(info)

        except Exception as e:
            logger.error(f"解析上舰数据出错: {e}")

    async def on_super_chat(self, event):
        """超级聊天（醒目留言）事件回调"""
        logger = self.app.logger
        try:
            logger.debug(f"+++++++++醒目留言: {event}")
            data = event["data"]["data"]

            #房间信息
            room_id = self.room_id
            owner_uid = self.room_info.get("owner_id")
            owner_name = self.room_info.get("owner_name")
            owner_face = self.room_info.get("owner_face")

            #发送者
            sender_uid = data.get("uid")
            user_info = data.get("user_info")
            sender_name = user_info.get("uname")
            sender_face = user_info.get("face")

            #醒目弹幕
            gift_info = data.get("gift")
            gift_type = 200
            gift_id = gift_info.get("gift_id")
            gift_name = gift_info.get("gift_name")
            gift_num = gift_info.get("num")
            gift_price = data.get("price") * data.get("rate")

            #message
            message = data.get("message")
            message_time = data.get("time")

            info = {
                "type": "super_chat",
                "room_id": room_id,
                "sender_uid" : sender_uid,
                "sender_name": sender_name,
                "sender_face": sender_face,
                "receiver_uid": owner_uid,
                "receiver_name": owner_name,
                "receiver_face": owner_face,
                "gift_id": gift_id,
                "gift_type": gift_type,
                "gift_name": gift_name,
                "gift_num": gift_num,
                "price": gift_price,
                "total_coin": (gift_num * gift_price),
                "blind_gift_id": 0,
                "blind_gift_name": "",
                "blind_gift_price": 0,
                "blind_gift_total": 0,
                "total_scope": (gift_num * gift_price),
                "message": message,
                "message_time":message_time  # 持续时间(秒)
            }
            logger.info(f"醒目留言: {data['user_info']['uname']} 留言: {data['message']} ￥{data['price']}")
            # 将弹幕放入消息队列
            self.message_queue.put(info)

            logger.debug(f"准备添加醒目留言到DB")
            from aibls.services.send_gift_service import send_gift_service
            if self.app:
                with self.app.app_context():
                    result, message = send_gift_service.add_send_gift(info)
            else:
                # 如果没传入 app，尝试使用 current_app
                from flask import current_app
                with current_app.app_context():
                    result, message = send_gift_service.add_send_gift(info)
            logger.debug(f"添加醒目留言记录结果：{result},{message}")

        except Exception as e:
            logger.error(f"解析醒目留言数据出错: {e}")


    async def on_user_video_link(self, event):
        """视频连线消息"""
        logger = self.app.logger
        try:
            logger.debug(f"*************视频连线：{event}")
            
        except Exception as e:
            logger.error(f"解析醒目留言数据出错: {e}")

    async def on_user_enter_v2(self, event):
        """(新版)进入直播间事件回调"""
        logger = self.app.logger
        try:
            logger.debug(f"***************进入直播间: {event}")
            # 新协议的数据结构通常如下，你可以打印出来看看具体字段
            data = event["data"].get('data', {})
            pb_decoded = data.get("pb_decoded", None)
            if pb_decoded is not None:
                user_id = str(pb_decoded.get("uid", None))
                user_name = str(pb_decoded.get("uname", None))
                user_info = pb_decoded.get("user_info", None)
                user_info_base = user_info.get("base", None)
                user_face = user_info_base.get("face", None)

                info = {
                    "type": "welcome",
                    "uname": user_name,
                    "uid": user_id,
                    "user_face": user_face,
                    "msg": f" 欢迎 {user_name} ({user_id}) 进入直播间！"
                }
                logger.info(f"用户进入房间消息：{info}")

                # 将弹幕放入消息队列
                self.message_queue.put(info)

                logger.info(f"准备查询VIP视频 {user_id}")
                # 2. 检查是否为VIP用户，发送视频播放指令
                # 在函数内部导入，避免循环导入
                from aibls.services.vip_service import vip_service
                if self.app:
                    with self.app.app_context():
                        vip_videos,error = vip_service.get_user_videos(user_id)
                else:
                    # 如果没传入 app，尝试使用 current_app
                    from flask import current_app
                    with current_app.app_context():
                        vip_videos,error = vip_service.get_user_videos(user_id)
                logger.info(f"查询到用户 {user_id}下的VIP视频数为:{len(vip_videos)}")

                if len(vip_videos) > 0:
                    video = random.choice(vip_videos)
                    video_url = video.get("url", "")
                    video_path = video.get("path", "")
                    video_title = video.get("title", "")
                    logger.info(f"VIP用户入场: {user_name} (UID: {user_id})，触发视频播放: {video.get('url', '')}")

                    video_command = {
                        "type": "video_command",  # 特殊类型，用于区分
                        "action": "play_video",
                        "video_url": video_url,  # 已经是Flask静态路径
                        "uid": user_id,
                        "video_path": video_path,
                        "video_name": video_title,
                        "timestamp": datetime.now().isoformat()
                    }
                    # 放入消息队列，由消费者推送到前端
                    self.message_queue.put(video_command)
        except Exception as e:
            logger.error(f"解析进入事件数据出错: {e}")

    async def on_user_enter(self, event):
        """(新版)进入直播间事件回调"""
        logger = self.app.logger
        try:
            logger.debug(f"$$$$$$$$$$$$$进入直播间: {event}")
            # 新协议的数据结构通常如下，你可以打印出来看看具体字段
            data = event["data"].get('data', {})

            # 注意：新版协议中用 'uid' 和 'open_id' 区分别，建议用 open_id
            # 安全获取用户信息
            user_id = str(data.get('open_id', data.get('uid', '0')))
            user_info = data.get('uinfo', None)
            user_name = ""
            if user_info is not None and user_id != 0:
                user_info_base = user_info.get('base', None)
                user_name = user_info_base.get('name', '未知用户')

            fans_medal_name = ""
            fans_level = 0
            guard_level = 0
            guard_name = ""

            #粉丝信息
            fans_info = data.get('medal', None)
            logger.debug(f"粉丝信息： {fans_info} ")
            if fans_info is not None:
                #灯牌信息
                fans_medal_name = fans_info.get('name', '')
                fans_level = fans_info.get('level', '')

                #舰长类型
                guard_level = fans_info.get('guard_level', 0)  # 0:无, 1:总督, 2:提督, 3:舰长
                guard_levels = {1: "总督", 2: "提督", 3: "舰长"}
                guard_name = guard_levels.get(guard_level, "")


            info = {
                "type": "welcome",
                "uname": user_name,
                "uid": user_id,
                "guard_name":guard_name,
                "fans_level":fans_level,
                "guard_level":guard_level,
                "fans_medal_name":fans_medal_name,
                "msg": f" 欢迎 {guard_name} {user_name} 进入直播间！"
            }
            logger.info(f"欢迎 {guard_name} {user_name} 进入直播间！")

            # 将弹幕放入消息队列
            self.message_queue.put(info)

            logger.info(f"准备查询VIP视频 {user_id}")
            # 2. 检查是否为VIP用户，发送视频播放指令
            # 在函数内部导入，避免循环导入
            from aibls.services.vip_service import vip_service
            if self.app:
                with self.app.app_context():
                    vip_videos,error = vip_service.get_user_videos(user_id)
            else:
                # 如果没传入 app，尝试使用 current_app
                from flask import current_app
                with current_app.app_context():
                    vip_videos,error = vip_service.get_user_videos(user_id)


            logger.info(f"查询到用户 {user_id}下的VIP视频数为{len(vip_videos)}")

            if len(vip_videos) > 0:
                video = random.choice(vip_videos)
                video_url = video.get("url", "")
                video_path = video.get("path", "")
                video_title = video.get("title", "")
                logger.info(f"VIP用户入场: {user_name} (UID: {user_id})，触发视频播放: {video.get('url', '')}")

                video_command = {
                    "type": "video_command",  # 特殊类型，用于区分
                    "action": "play_video",
                    "video_url": video_url,  # 已经是Flask静态路径
                    "uid": user_id,
                    "video_path": video_path,
                    "video_name": video_title,
                    "timestamp": datetime.now().isoformat()
                }
                # 放入消息队列，由消费者推送到前端
                self.message_queue.put(video_command)

        except Exception as e:
            logger.error(f"解析进入事件数据出错: {e}")


    async def load_user_info(self,user_id):
        user_obj = user.User(user_id,self.credential)
        user_info = await user_obj.get_user_info()
        print(user_info)
        return user_info