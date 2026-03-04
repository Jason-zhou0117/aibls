import asyncio

import logging
import random
import threading
from datetime import datetime

from bilibili_api import Credential, live, sync, user

logger = logging.getLogger(__name__)


class AsyncMessageGenerator:
    """异步消息生成器 - 在单个线程中使用 asyncio.new_event_loop"""

    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.loop = None
        self.thread = None
        self.running = False
        self.generator_id = random.randint(1000, 9999)

    def connect(self, user_credential: Credential, room_id: int):
        self.credential = user_credential
        self.room_id = room_id
        self._room = live.LiveDanmaku(room_id, False, self.credential)

    def start(self):
        """启动消息生成器线程"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._run_async_loop)
            self.thread.daemon = True
            self.thread.name = f"异步调用B站弹幕-{self.generator_id}"
            self.thread.start()
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 消息生成器 {self.generator_id} 已启动")
            return True
        return False

    def stop(self):
        """停止消息生成器"""
        self.running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 消息生成器 {self.generator_id} 已停止")

    def _run_async_loop(self):
        """在新线程中运行异步事件循环"""
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
        self._room.add_event_listener("DANMU_MSG", self.on_danmaku) #普通弹幕
        self._room.add_event_listener("SEND_GIFT", self.on_gift)  # 赠送礼物
        self._room.add_event_listener("GUARD_BUY", self.on_buy_guard)  # 购买舰长
        self._room.add_event_listener("SUPER_CHAT_MESSAGE", self.on_super_chat)  # 醒目留言
        self._room.add_event_listener("INTERACT_WORD", self.on_interaction)  # 用户进入直播间
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
        try:

            logger.info(f"文字弹幕，原始数据: {event}")
            # 获取弹幕数据
            info = event['data']['info']

            # 解析用户信息
            user_info = info[2]  # 用户信息数组

            # 解析弹幕内容 - info[1] 是弹幕文本
            msg = info[1]

            # 解析用户ID和昵称
            uid = user_info[0]
            uname = user_info[1]
            #获取用户详情
            user_detail = await self.load_user_info(uid)

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
                "msg": msg,  # 弹幕内容 (info[1])
                "uname": uname,  # 用户昵称
                "uid": uid,  # 用户ID
                "user_face" : user_detail["face"] if user_detail is not None else "",
                "timestamp": timestamp,  # 时间戳
                "send_time":dt_str,
                "medal_name": medal_name,  # 粉丝牌名称
                "medal_level":medal_level,  # 粉丝牌等级
                "honor_level":honor_level,
                "raw_info": info  # 保留原始数据（可选）
            }

            # 调试输出
            logger.info(f"弹幕-文字: {uname}: {msg} [粉丝牌: {medal_name} Lv.{medal_level}]")

            self.message_queue.put(danmu_data)
        except Exception as e:
            logger.error(f"解析弹幕数据出错: {e}")
            logger.info(f"文字弹幕，原始数据: {event}")

    async def _parse_datetime_str_(self,timestamp) -> str:
        if timestamp > 10 ** 10:  # 判断是否为毫秒（大于10位数）
            timestamp = timestamp / 1000
        dt = datetime.fromtimestamp(timestamp)
        dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        return dt_str

    async def on_gift(self, event):
        """礼物事件回调"""
        try:

            logger.info(f"礼物弹幕，原始数据: {event}")

            data = event["data"]["data"]
            print(data)
            gift_info =  data["gift_info"]
            gift_img = gift_info["gif"] if "gif" in gift_info else gift_info["img_basic"]
            print(gift_img)
            #粉丝灯牌
            medal_info = data["medal_info"]
            medal_name = medal_info["medal_name"] if medal_info is not None and "medal_name" in medal_info else ""
            medal_level = medal_info["medal_level"] if medal_info is not None and "medal_level" in medal_info else 0
            print(f"投喂-粉丝灯牌{gift_img}")

            send_user  = data["sender_uinfo"]["base"]
            user_face = send_user["face"] if send_user is not None and "face" in send_user else ""
            print(f"投喂-用户头像{user_face}")
            # 礼物数据结构: https://github.com/Nemo2011/bilibili-api/blob/main/bilibili_api/live.py
            info = {
                "type": "gift",
                "msg": f"弹幕-礼物: {data['uname']} {data['action']} {data['giftName']} x{data['num']}",  # 弹幕内容 (info[1])
                "uname": data["uname"],
                "uid": data["uid"],
                "user_face" : user_face,
                "medal_name": medal_name,  # 粉丝牌名称
                "medal_level":medal_level,  # 粉丝牌等级 粉丝牌等级
                "gift_name": data["giftName"],
                "gift_img": gift_img,
                "gift_num": data["num"],
                "action": data["action"],  # 赠送动作，如 "赠送"
                "price": data["price"],  # 单价 (金瓜子)
                "total_coin": data["total_coin"] ,
                "raw_info": event
            }
            logger.info(f"弹幕-礼物: {data['uname']} {data['action']} {data['giftName']} x{data['num']}")

            #将弹幕放入消息队列
            self.message_queue.put(info)

        except Exception as e:
            logger.error(f"解析礼物数据出错: {e}")

    async def on_buy_guard(self, event):
        """上舰事件回调"""
        try:
            data = event["data"]["data"]
            # 舰长等级对应: 3=舰长, 2=提督, 1=总督
            guard_level_names = {1: "总督", 2: "提督", 3: "舰长"}
            guard_name = guard_level_names.get(data["guard_level"], "未知")

            info = {
                "type": "guard",
                "msg": f"{data['username']} 开通 {guard_name} x {data["num"]} 个月",
                "uname": data["username"],
                "uid": data["uid"],
                "guard_level": data["guard_level"],
                "guard_name": guard_name,
                "num": data["num"]
            }
            logger.info(f"上舰: {data['username']} 开通{guard_name}")

            #将弹幕放入消息队列
            self.message_queue.put(info)

        except Exception as e:
            logger.error(f"解析上舰数据出错: {e}")
            logger.info(f"文字弹幕，原始数据: {event}")

    async def on_super_chat(self, event):
        """超级聊天（醒目留言）事件回调"""
        try:
            data = event["data"]["data"]
            info = {
                "type": "super_chat",
                "msg": data["message"],
                "uname": data["user_info"]["uname"],
                "uid": data["uid"],
                "price": data["price"],  # 金额(元)
                "time": data["time"]  # 持续时间(秒)
            }
            logger.info(f"醒目留言: {data['user_info']['uname']} 留言: {data['message']} ￥{data['price']}")

            # 将弹幕放入消息队列
            self.message_queue.put(info)
        except Exception as e:
            logger.error(f"解析醒目留言数据出错: {e}")
            logger.info(f"文字弹幕，原始数据: {event}")

    async def on_interaction(self, event):
        """进入直播间事件回调"""
        try:
            data = event["data"]["data"]
            info = {
                "type": "welcome",
                "uname": data["uname"],
                "uid": data["uid"],
                "msg": f"欢迎 {data['uname']} 进入直播间"
            }
            logger.info(f"进入: {data['uname']} 进入直播间")

            # 将弹幕放入消息队列
            self.message_queue.put(info)
        except Exception as e:
            logger.error(f"解析进入事件数据出错: {e}")
            logger.info(f"文字弹幕，原始数据: {event}")

    async def load_user_info(self,user_id):
        user_obj = user.User(user_id,self.credential)
        user_info = await user_obj.get_user_info()
        print(user_info)
        return user_info