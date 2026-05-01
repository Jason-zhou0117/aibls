# aibls/services/message_consumer.py
import logging
import queue
import time
from datetime import datetime

from aibls.stock_io import socketio, message_queue


class MessageConsumer:
    """消息消费者 - 独立线程运行"""

    def __init__(self, app=None):
        self.running = True
        self.app = app  # 保存 app 实例
        self.logger = None
        self.stats = {
            'total_pushed': 0,
            'last_push_time': None,
            'queue_size_history': []
        }
        self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        if self.app:
            self.logger = self.app.logger
        else:
            # 如果没有 app，创建一个独立的 logger
            self.logger = logging.getLogger('MessageConsumer')
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.DEBUG)

    def run(self):
        """运行消费者"""
        self.logger.debug(f"[{datetime.now().strftime('%H:%M:%S')}] 消息消费者线程已启动")

        while self.running:
            try:
                self._process_one_message()
            except Exception as e:
                self.logger.error(f"消费消息错误: {e}")
                time.sleep(0.5)

    def _process_one_message(self):
        """处理单条消息"""
        try:
            if message_queue.empty():
                time.sleep(0.1)
                return

            message = message_queue.get(timeout=0.5)
            self._push_message(message)
            message_queue.task_done()

        except queue.Empty:
            time.sleep(0.1)

    def _push_message(self, message):
        """推送消息到前端"""
        try:
            message['pushed_at'] = datetime.now().isoformat()
            self.logger.info(f"推送消息: {message}")

            msg_type = message.get("type")

            if msg_type == "video_command":
                # 在独立线程中发送 SocketIO 消息需要使用 app 上下文
                if self.app:
                    with self.app.app_context():
                        socketio.emit('video_command', message)
                else:
                    socketio.emit('video_command', message)
                self.logger.info(f"已推送视频指令: {message.get('uname')}")
            else:
                if self.app:
                    with self.app.app_context():
                        socketio.emit(msg_type, message)
                else:
                    socketio.emit(msg_type, message)

            # 更新统计
            self.stats['total_pushed'] += 1
            self.stats['last_push_time'] = datetime.now().isoformat()
            self.stats['queue_size_history'].append(message_queue.qsize())

            if len(self.stats['queue_size_history']) > 50:
                self.stats['queue_size_history'].pop(0)

        except Exception as e:
            self.logger.error(f"推送消息错误: {e}")

    def stop(self):
        """停止消费者"""
        self.running = False


# 全局消费者实例（初始为 None，需要在 app 初始化后设置）
message_consumer = None