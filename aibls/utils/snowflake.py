import time
import threading


class Snowflake:
    """
    纯Python实现的雪花算法工具类
    64位ID结构：1位符号位(0) + 41位时间戳 + 10位机器ID + 12位序列号
    """

    def __init__(self, worker_id=1, data_center_id=1, sequence=0):
        """
        初始化雪花算法生成器
        :param worker_id: 机器ID (0-31)
        :param data_center_id: 数据中心ID (0-31)
        :param sequence: 起始序列号
        """
        self.worker_id = worker_id
        self.data_center_id = data_center_id
        self.sequence = sequence
        self.last_timestamp = -1
        self.lock = threading.Lock()  # 保证线程安全

        # 定义各部分的位数
        self.worker_id_bits = 5  # 机器ID占5位
        self.data_center_id_bits = 5  # 数据中心ID占5位
        self.sequence_bits = 12  # 序列号占12位

        # 计算最大值
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)  # 31
        self.max_data_center_id = -1 ^ (-1 << self.data_center_id_bits)  # 31
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)  # 4095

        # 验证worker_id和data_center_id是否超出范围
        if worker_id > self.max_worker_id or worker_id < 0:
            raise ValueError(f"worker ID 必须在 0-{self.max_worker_id} 之间")
        if data_center_id > self.max_data_center_id or data_center_id < 0:
            raise ValueError(f"data center ID 必须在 0-{self.max_data_center_id} 之间")

        # 起始时间戳（2020-01-01 00:00:00 UTC，可自定义）
        self.tw_epoch = 1577808000000

        # 计算位移量
        self.worker_id_shift = self.sequence_bits  # 12
        self.data_center_id_shift = self.sequence_bits + self.worker_id_bits  # 17
        self.timestamp_shift = self.sequence_bits + self.worker_id_bits + self.data_center_id_bits  # 22

    def _wait_for_next_millis(self, last_timestamp):
        """自旋等待到下一毫秒"""
        timestamp = self._gen_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._gen_timestamp()
        return timestamp

    def _gen_timestamp(self):
        """生成当前时间戳（毫秒级）"""
        return int(time.time() * 1000)

    def next_id(self):
        """
        生成下一个唯一ID（线程安全）
        :return: 64位整数ID
        """
        with self.lock:
            timestamp = self._gen_timestamp()

            # 处理时钟回拨
            if timestamp < self.last_timestamp:
                raise Exception(f"时钟回拨拒绝生成ID，回退 {self.last_timestamp - timestamp} 毫秒")

            # 同一毫秒内
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                # 当前毫秒序列号用完，等待下一毫秒
                if self.sequence == 0:
                    timestamp = self._wait_for_next_millis(self.last_timestamp)
            else:
                # 不同毫秒，重置序列号
                self.sequence = 0

            self.last_timestamp = timestamp

            # 组合生成ID
            snowflake_id = ((timestamp - self.tw_epoch) << self.timestamp_shift) | \
                           (self.data_center_id << self.data_center_id_shift) | \
                           (self.worker_id << self.worker_id_shift) | \
                           self.sequence
            return snowflake_id

    def parse_id(self, snowflake_id):
        """
        解析ID中包含的信息
        :param snowflake_id: 生成的ID
        :return: 包含时间戳、机器ID、序列号等信息的字典
        """
        # 提取各段的值
        sequence = snowflake_id & self.max_sequence
        worker_id = (snowflake_id >> self.worker_id_shift) & self.max_worker_id
        data_center_id = (snowflake_id >> self.data_center_id_shift) & self.max_data_center_id
        timestamp = (snowflake_id >> self.timestamp_shift) + self.tw_epoch

        # 转换为可读时间
        from datetime import datetime
        readable_time = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        return {
            'snowflake_id': snowflake_id,
            'timestamp': timestamp,
            'readable_time': readable_time,
            'data_center_id': data_center_id,
            'worker_id': worker_id,
            'sequence': sequence
        }

