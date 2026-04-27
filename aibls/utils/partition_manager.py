from sqlalchemy import text
from flask import current_app
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PartitionManager:
    """分区管理工具类"""

    @staticmethod
    def get_future_months(start_date, months):
        """获取未来几个月的月份列表"""
        months_list = []
        current = start_date.replace(day=1)

        for i in range(months):
            if i > 0:
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            months_list.append(current)

        return months_list

    @staticmethod
    def get_partition_name(date):
        """根据日期获取分区名"""
        return f"p{date.strftime('%Y%m')}"

    @staticmethod
    def get_partition_boundary(date):
        """获取分区的边界日期（下个月的第一天）"""
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1, day=1)
        else:
            return date.replace(month=date.month + 1, day=1)

    @staticmethod
    def create_initial_partitions(db, table_name, start_date, months):
        """创建初始分区"""
        try:
            months_list = PartitionManager.get_future_months(start_date, months)
            partitions = []

            for i, month_date in enumerate(months_list):
                partition_name = PartitionManager.get_partition_name(month_date)
                boundary_date = PartitionManager.get_partition_boundary(month_date)

                if i < len(months_list) - 1:
                    partitions.append(
                        f"PARTITION {partition_name} VALUES LESS THAN (TO_DAYS('{boundary_date.strftime('%Y-%m-%d')}'))")
                else:
                    # 最后一个分区用MAXVALUE
                    partitions.append(f"PARTITION {partition_name} VALUES LESS THAN MAXVALUE")

            # 创建表的SQL
            create_sql = f"""
                CREATE TABLE {table_name} (
                    id BIGINT NOT NULL AUTO_INCREMENT,
                    user_id VARCHAR(100) NOT NULL,
                    user_name VARCHAR(100) NOT NULL,
                    user_face VARCHAR(500),
                    medal_level INT DEFAULT 0,
                    medal_name VARCHAR(100),
                    room_id VARCHAR(50) NOT NULL,
                    room_title VARCHAR(200),
                    message TEXT NOT NULL,
                    sendtime DATETIME NOT NULL,
                    createat DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id, send_time),
                    INDEX idx_room_sendtime (room_id, sendtime),
                    INDEX idx_user_sendtime (user_id, sendtime),
                    FULLTEXT INDEX idx_message (message)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                PARTITION BY RANGE (TO_DAYS(sendtime))
                (
                    {', '.join(partitions)}
                );
            """

            db.session.execute(text(create_sql))
            db.session.commit()
            logger.info(f"Created table {table_name} with {months} partitions")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create initial partitions: {str(e)}")
            raise

    @staticmethod
    def add_new_partitions(db, table_name, months=3):
        """添加新分区"""
        try:
            # 获取当前最大分区
            check_sql = text(f"""
                SELECT PARTITION_NAME, PARTITION_DESCRIPTION
                FROM information_schema.PARTITIONS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table_name}'
                AND PARTITION_DESCRIPTION != 'MAXVALUE'
                ORDER BY PARTITION_ORDINAL_POSITION DESC
                LIMIT 1
            """)

            result = db.session.execute(check_sql).first()

            if not result:
                logger.warning(f"No partitions found for {table_name}")
                return

            last_partition = result[0]
            if last_partition.startswith('p'):
                last_year_month = last_partition[1:7]
                last_date = datetime.strptime(last_year_month, '%Y%m')

                # 从下个月开始添加新分区
                current = PartitionManager.get_partition_boundary(last_date)
                new_partitions = []

                for i in range(months):
                    partition_name = PartitionManager.get_partition_name(current)
                    next_boundary = PartitionManager.get_partition_boundary(current)

                    if i < months - 1:
                        new_partitions.append(
                            f"ADD PARTITION (PARTITION {partition_name} VALUES LESS THAN (TO_DAYS('{next_boundary.strftime('%Y-%m-%d')}')))"
                        )
                    else:
                        # 最后一个分区用MAXVALUE
                        new_partitions.append(
                            f"ADD PARTITION (PARTITION {partition_name} VALUES LESS THAN MAXVALUE)"
                        )

                    current = next_boundary

                # 执行添加分区
                if new_partitions:
                    alter_sql = f"ALTER TABLE {table_name} {', '.join(new_partitions)}"
                    db.session.execute(text(alter_sql))
                    db.session.commit()
                    logger.info(f"Added {months} new partitions to {table_name}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to add partitions: {str(e)}")
            raise

    @staticmethod
    def drop_old_partitions(db, table_name, months_to_keep):
        """删除旧分区"""
        try:
            # 计算要保留的最早月份
            now = datetime.now()
            earliest_to_keep = PartitionManager.get_previous_month(now, months_to_keep)

            # 获取所有分区信息
            check_sql = text(f"""
                SELECT PARTITION_NAME
                FROM information_schema.PARTITIONS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table_name}'
                AND PARTITION_DESCRIPTION != 'MAXVALUE'
                ORDER BY PARTITION_ORDINAL_POSITION
            """)

            partitions = db.session.execute(check_sql).fetchall()

            dropped = []
            for partition in partitions:
                partition_name = partition[0]
                if partition_name.startswith('p'):
                    year_month = partition_name[1:7]
                    partition_date = datetime.strptime(year_month, '%Y%m')

                    if partition_date < earliest_to_keep:
                        drop_sql = text(f"ALTER TABLE {table_name} DROP PARTITION {partition_name}")
                        db.session.execute(drop_sql)
                        dropped.append(partition_name)

            db.session.commit()

            if dropped:
                logger.info(f"Dropped old partitions: {', '.join(dropped)}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to drop old partitions: {str(e)}")

    @staticmethod
    def get_previous_month(date, months):
        """获取前几个月的日期"""
        year = date.year
        month = date.month - months

        while month <= 0:
            year -= 1
            month += 12

        return datetime(year, month, 1)

    @staticmethod
    def get_partition_info(db, table_name):
        """获取分区信息"""
        try:
            sql = text(f"""
                SELECT 
                    PARTITION_NAME,
                    PARTITION_ORDINAL_POSITION,
                    PARTITION_METHOD,
                    PARTITION_EXPRESSION,
                    PARTITION_DESCRIPTION,
                    TABLE_ROWS,
                    AVG_ROW_LENGTH,
                    DATA_LENGTH
                FROM information_schema.PARTITIONS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = '{table_name}'
                ORDER BY PARTITION_ORDINAL_POSITION
            """)

            results = db.session.execute(sql).fetchall()

            partitions = []
            for row in results:
                partitions.append({
                    'name': row[0],
                    'position': row[1],
                    'method': row[2],
                    'expression': row[3],
                    'description': row[4],
                    'rows': row[5],
                    'avg_row_length': row[6],
                    'data_length': row[7]
                })

            return partitions

        except Exception as e:
            logger.error(f"Failed to get partition info: {str(e)}")
            return []