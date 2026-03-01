import asyncio
import logging
import threading

from bilibili_api import Credential, live, sync

logger = logging.getLogger(__name__)

class DanmuListener:

    def __init__(self,login_user_credential:Credential,room_id:int,message_callback) -> None:
        super().__init__()
        self.login_user_credential = login_user_credential
        self.room_id = room_id
        self.callback = message_callback
        #self.daemon = True  # 设置为守护线程，主程序退出时自动结束
        self.running = True
        self.loop = None
        self.thread = None

    def start2(self):
        """线程入口函数"""
        # 为每个线程创建独立的事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 运行异步的弹幕监听
        self.loop.run_until_complete(self._listen_danmu())

    async def _listen_danmu(self):
        """异步监听弹幕"""
        try:
            # 创建直播间对象
            room = live.LiveDanmaku(self.room_id,False,self.login_user_credential)
            # 注册弹幕事件监听器
            room.add_event_listener('DANMU_MSG', self._on_text_message)
            room.add_event_listener('SEND_GIFT', self._on_send_gift)
            room.add_event_listener('WELCOME', self._on_send_gift)

            logger.info(f"开始监听直播间 {self.room_id}...")

            # 连接并开始监听
            await self.room.connect()

            # 保持连接，直到线程被停止
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"弹幕监听出错 (房间{self.room_id}): {e}")
            # 尝试重新连接
            if self.running:
                await asyncio.sleep(5)
                await self._listen_danmu()

    def stop2(self):
        """停止监听"""
        self.running = False
        if self.loop:
            self.loop.stop()



    def start(self):
        """启动监听器（非阻塞）"""
        if self.thread and self.thread.is_alive():
            print("监听器已在运行中")
            return

        self.thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self.thread.start()
        print("弹幕监听线程已启动")

    def _run_in_thread(self):
        """在独立线程中运行异步事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.running = True

        try:
            self.loop.run_until_complete(self._run_listener())
        except Exception as e:
            print(f"事件循环错误: {e}")
        finally:
            self.loop.close()
            self.running = False

    async def _run_listener(self):
        """异步运行弹幕监听"""
        try:
            # 创建直播弹幕客户端
            self.room = live.LiveDanmaku(self.room_id)

            # 注册弹幕事件监听器
            self.room.add_event_listener('DANMU_MSG', self._on_text_message)

            print(f"开始连接直播间 {self.room_id}...")

            # 连接并开始接收弹幕（这是一个长连接，会一直运行）
            await self.room.connect()

        except Exception as e:
            print(f"弹幕连接错误: {e}")
        finally:
            self.running = False

    def stop(self):
        """停止监听器"""
        self.running = False
        if self.room:
            # 这里需要根据bilibili-api的实际方法调整
            pass

    async def _on_text_message(self,event):
        """
        处理文字弹幕消息
        :param event: 消息的内容
            event['data']['info'][1]消息的文字
            event['data']['info'][2]发送消息的用户
            event['data']['info'][2][0]发送消息用户的UID
            event['data']['info'][2][1]发送消息用户的名字
            event['data']['info'][9][ts]发送消息时间戳
        :return:
        """
        try:
            # 解析弹幕数据
            # event数据结构参考bilibili-api文档
            danmu_data = event['data']

            # 提取关键信息
            info = danmu_data['info']
            danmu_text = info[1]  # 弹幕内容
            user_info = info[2]
            user_name = user_info[1]  # 用户名
            user_id = user_info[0]  # 用户ID

            # 构建要发送到前端的消息
            message = {
                'type': 'danmu',
                'room_id': self.room_id,
                'user': {
                    'id': user_id,
                    'name': user_name
                },
                'content': danmu_text,
                'time': info[9]['ts'] if len(info) > 9 else None
            }

            # 打印到控制台（调试用）
            logger.debug(f"[房间{self.room_id}] {user_name}: {danmu_text}")

            # 通过SocketIO推送到前端
            if self.callback:
                self.callback('new_danmu',message)


        except Exception as e:
            logger.error(f"处理弹幕消息失败: {e}")

    async def _on_send_gift(self,event):
        try:
            logger.debug("送礼物的消息：{}".format(event))
            """
            处理礼物消息
            :param event: 消息的数据
                event['data']['data']['uname']
                event['data']['data']['giftName']
                event['data']['data']['num']
            :return:
            """
            data = event['data']['data']
            message = {
                'type': 'gift',
                'room_id': self.room_id,
                'user': data['uname'],
                'gift': data['giftName'],
                'num': data['num']
            }
            logger.debug(f"[礼物] {data['uname']} 赠送 {data['giftName']} x{data['num']}")

            # 通过SocketIO推送到前端
            if self.callback:
                self.callback('new_danmu', message)
        except Exception as e:
            logger.error(f"处理发送礼物的弹幕消息失败: {e}")

    async def _on_welcome(self,event):
        """
        欢迎进入房间
        :param event: 弹幕事件的数据
            event['data']['uname']
        :return:
        """
        try:
            logger.debug("用户进入房间：{}".format(event))
            data = event['data']
            message = {
                'type': 'welcome',
                'room_id': self.room_id,
                'user': data['uname']
            }
            if self.callback:
                self.callback('new_danmu', message)
        except Exception as e:
            logger.error(f"处理用户进入房间的弹幕失败: {e}")


class BilibiliDanmuListener:
    def __init__(self, login_user_credential:Credential,room_id, callback_func):
        """
        :param room_id: 直播间ID
        :param callback_func: 收到弹幕后的回调函数，接收一个dict参数
        """
        self.room_id = room_id
        self.callback = callback_func
        self.room = live.LiveDanmaku(room_id,False,login_user_credential)
        self.is_running = False
        self.thread = None

    def on_danmaku(self, event):
        """
        弹幕事件回调 (由bilibili-api触发)
        正确的事件数据结构：
        """
        try:
            # 获取弹幕数据
            info = event['data']['info']

            # 解析用户信息
            user_info = info[2]  # 用户信息数组

            # 解析弹幕内容 - info[1] 是弹幕文本
            msg = info[1]

            # 解析用户ID和昵称
            uid = user_info[0]
            uname = user_info[1]

            # 解析粉丝牌信息 (如果有)
            medal_info = info[3] if len(info) > 3 else []
            medal_name = medal_info[1] if len(medal_info) > 1 else ""
            medal_level = medal_info[0] if len(medal_info) > 0 else 0

            # 解析弹幕时间戳
            timestamp = info[0][4] if len(info[0]) > 4 else 0

            # 构建标准化弹幕数据
            danmu_data = {
                "type": "danmaku",
                "msg": msg,  # 弹幕内容 (info[1])
                "uname": uname,  # 用户昵称
                "uid": uid,  # 用户ID
                "timestamp": timestamp,  # 时间戳
                "medal_name": medal_name,  # 粉丝牌名称
                "medal_level": medal_level,  # 粉丝牌等级
                "raw_info": info  # 保留原始数据（可选）
            }

            # 调试输出
            print(f"弹幕: {uname}: {msg} [粉丝牌: {medal_name} Lv.{medal_level}]")
            # 调用回调函数
            if self.callback:
                self.callback("new_danmu",danmu_data)


        except Exception as e:
            print(f"解析弹幕数据出错: {e}")
            print(f"原始数据: {event}")

    def on_gift(self, event):
        """礼物事件回调"""
        try:
            data = event["data"]

            # 礼物数据结构: https://github.com/Nemo2011/bilibili-api/blob/main/bilibili_api/live.py
            info = {
                "type": "gift",
                "uname": data["uname"],
                "uid": data["uid"],
                "gift_name": data["giftName"],
                "num": data["num"],
                "action": data["action"],  # 赠送动作，如 "赠送"
                "price": data["price"],  # 单价 (金瓜子)
                "total_coin": data["total_coin"]  # 总价值
            }
            if self.callback:
                self.callback(info)
            print(f"礼物: {data['uname']} {data['action']} {data['giftName']} x{data['num']}")

        except Exception as e:
            print(f"解析礼物数据出错: {e}")

    def on_buy_guard(self, event):
        """上舰事件回调"""
        try:
            data = event["data"]
            # 舰长等级对应: 3=舰长, 2=提督, 1=总督
            guard_level_names = {1: "总督", 2: "提督", 3: "舰长"}
            guard_name = guard_level_names.get(data["guard_level"], "未知")

            info = {
                "type": "guard",
                "uname": data["username"],
                "uid": data["uid"],
                "guard_level": data["guard_level"],
                "guard_name": guard_name,
                "num": data["num"]
            }
            if self.callback:
                self.callback(info)
            print(f"上舰: {data['username']} 开通{guard_name}")

        except Exception as e:
            print(f"解析上舰数据出错: {e}")

    def on_super_chat(self, event):
        """超级聊天（醒目留言）事件回调"""
        try:
            data = event["data"]
            info = {
                "type": "super_chat",
                "uname": data["user_info"]["uname"],
                "uid": data["uid"],
                "msg": data["message"],
                "price": data["price"],  # 金额(元)
                "time": data["time"]  # 持续时间(秒)
            }
            if self.callback:
                self.callback(info)
            print(f"醒目留言: {data['user_info']['uname']} 留言: {data['message']} ￥{data['price']}")

        except Exception as e:
            print(f"解析醒目留言数据出错: {e}")

    def on_interaction(self, event):
        """进入直播间事件回调"""
        try:
            data = event["data"]
            info = {
                "type": "interaction",
                "uname": data["uname"],
                "uid": data["uid"],
                "msg": f"欢迎 {data['uname']} 进入直播间"
            }
            if self.callback:
                self.callback(info)
            print(f"进入: {data['uname']} 进入直播间")

        except Exception as e:
            print(f"解析进入事件数据出错: {e}")

    def _run_loop(self):
        """在独立线程中运行异步事件循环"""
        # 为线程创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 注册事件回调
        self.room.add_event_listener("DANMU_MSG", self.on_danmaku)  # 弹幕消息
        self.room.add_event_listener("SEND_GIFT", self.on_gift)  # 赠送礼物
        self.room.add_event_listener("GUARD_BUY", self.on_buy_guard)  # 购买舰长
        self.room.add_event_listener("SUPER_CHAT_MESSAGE", self.on_super_chat)  # 醒目留言
        self.room.add_event_listener("INTERACT_WORD", self.on_interaction)  # 用户进入直播间

        try:
            # 连接并开始监听
            sync(self.room.connect())
        except Exception as e:
            print(f"监听连接出错: {e}")
            self.is_running = False

    def start(self):
        """启动监听（非阻塞）"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print(f"开始监听直播间 {self.room_id}")

    def stop(self):
        """停止监听"""
        if self.is_running:
            self.is_running = False
            # 注意：需要异步断开连接
            if self.room:
                try:
                    # 创建一个新的事件循环来执行断开连接
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    sync(self.room.disconnect())
                    loop.close()
                except:
                    pass
            print("监听已停止")