import uuid

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index, text, CHAR, Column, String, Integer, Text, DateTime

from aibls.models.base import BaseModel

db = SQLAlchemy()


class Danmaku(BaseModel):
    """弹幕模型 - 使用MySQL分区表"""
    __tablename__ = 'danmaku_info'

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False)
    user_name = Column(String(100), nullable=False)
    user_face = Column(String(500))
    medal_level = Column(Integer, default=0)
    medal_name = Column(String(100))
    room_id = Column(String(50), nullable=False)
    room_title = Column(String(200))
    message = Column(Text, nullable=False)
    send_time = Column(DateTime, nullable=False)

    # 创建索引
    __table_args__ = (
        Index('idx_room_id_send_time', 'room_id', 'send_time'),
        Index('idx_user_id_send_time', 'user_id', 'send_time'),
        Index('idx_send_time', 'send_time'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'extend_existing': True
        }
    )

    @staticmethod
    def create_partitioned_table():
        """创建分区表（如果不存在）"""
        # 检查表是否存在
        check_sql = text("""
                         SELECT COUNT(*)
                         FROM information_schema.tables
                         WHERE table_schema = :db_name
                           AND table_name = 'danmaku'
                         """)

        from flask import current_app
        result = db.session.execute(
            check_sql,
            {'db_name': current_app.config['DB_NAME']}
        ).scalar()

        if not result:
            # 创建分区表，初始创建6个分区（当前月+未来5个月）
            create_sql = text("""
                              CREATE TABLE danmaku
                              (
                                  id          BIGINT AUTO_INCREMENT,
                                  user_id     VARCHAR(100) NOT NULL,
                                  user_name   VARCHAR(100) NOT NULL,
                                  user_face   VARCHAR(500),
                                  medal_level INT                   DEFAULT 0,
                                  medal_name  VARCHAR(100),
                                  room_id     VARCHAR(50)  NOT NULL,
                                  room_title  VARCHAR(200),
                                  message     TEXT         NOT NULL,
                                  sendtime    DATETIME     NOT NULL,
                                  createat    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                  PRIMARY KEY (id, sendtime),
                                  INDEX       idx_room_id_sendtime (room_id, sendtime),
                                  INDEX       idx_user_id_sendtime (user_id, sendtime),
                                  INDEX       idx_sendtime (sendtime)
                              ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                PARTITION BY RANGE (TO_DAYS(sendtime))
                (
                    PARTITION p_future VALUES LESS THAN MAXVALUE
                );
                              """)

            try:
                db.session.execute(create_sql)
                db.session.commit()

                # 初始化分区
                current_date = datetime.now()
                Danmaku.add_months_partitions(current_date, 6)

                print("Created partitioned table danmaku")
            except Exception as e:
                db.session.rollback()
                print(f"Failed to create table: {str(e)}")
                raise

    @staticmethod
    def add_months_partitions(start_date, months=3):
        """
        添加未来几个月的新分区
        :param start_date: 开始日期
        :param months: 要添加的月数
        """
        try:
            # 先删除p_future分区
            drop_future_sql = text("ALTER TABLE danmaku REORGANIZE PARTITION p_future INTO ();")
            db.session.execute(drop_future_sql)

            # 计算分区边界
            partitions = []
            current = start_date.replace(day=1)

            for i in range(months + 1):
                if i == 0:
                    # 当前月
                    partition_name = f"p{current.strftime('%Y%m')}"
                    next_month = Danmaku._get_next_month(current)
                    boundary = f"TO_DAYS('{next_month.strftime('%Y-%m-%d')}')"
                    partitions.append(f"PARTITION {partition_name} VALUES LESS THAN ({boundary})")
                else:
                    # 未来月份
                    current = Danmaku._get_next_month(current)
                    partition_name = f"p{current.strftime('%Y%m')}"
                    next_month = Danmaku._get_next_month(current)
                    boundary = f"TO_DAYS('{next_month.strftime('%Y-%m-%d')}')"
                    partitions.append(f"PARTITION {partition_name} VALUES LESS THAN ({boundary})")

            # 重新创建所有分区
            alter_sql = f"""
                ALTER TABLE danmaku REORGANIZE PARTITION p_future INTO (
                    {', '.join(partitions)},
                    PARTITION p_future VALUES LESS THAN MAXVALUE
                );
            """

            db.session.execute(text(alter_sql))
            db.session.commit()
            print(f"Added {months} new partitions")

        except Exception as e:
            db.session.rollback()
            print(f"Failed to add partitions: {str(e)}")
            raise

    @staticmethod
    def _get_next_month(date):
        """获取下个月的第一天"""
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1, day=1)
        else:
            return date.replace(month=date.month + 1, day=1)

    @staticmethod
    def drop_old_partitions(months_to_keep=6):
        """
        删除旧分区
        :param months_to_keep: 保留最近几个月的数据
        """
        try:
            # 获取当前时间
            now = datetime.now()
            # 计算要保留的最早月份
            earliest_to_keep = Danmaku._get_previous_month(now, months_to_keep)

            # 获取所有分区信息
            check_sql = text("""
                             SELECT PARTITION_NAME, PARTITION_DESCRIPTION
                             FROM information_schema.PARTITIONS
                             WHERE TABLE_SCHEMA = DATABASE()
                               AND TABLE_NAME = 'danmaku'
                               AND PARTITION_NAME != 'p_future'
                             """)

            partitions = db.session.execute(check_sql).fetchall()

            for partition in partitions:
                partition_name = partition[0]
                # 从分区名获取年月（格式：p202401）
                if partition_name.startswith('p'):
                    year_month = partition_name[1:7]
                    partition_date = datetime.strptime(year_month, '%Y%m')

                    # 如果分区月份早于要保留的最早月份，则删除
                    if partition_date < earliest_to_keep:
                        drop_sql = text(f"ALTER TABLE danmaku DROP PARTITION {partition_name}")
                        db.session.execute(drop_sql)
                        print(f"Dropped old partition: {partition_name}")

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Failed to drop old partitions: {str(e)}")
            raise

    @staticmethod
    def _get_previous_month(date, months):
        """获取前几个月的日期"""
        year = date.year
        month = date.month - months

        while month <= 0:
            year -= 1
            month += 12

        return datetime(year, month, 1)