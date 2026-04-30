# aibls/db_init.py
from aibls.models.database import db
from aibls.utils.migrate_json_to_db import migrate_json_to_db

# 添加全局标志，避免重复创建表
_tables_created = False


def init_db(app):
    """初始化数据库"""
    global _tables_created

    db.init_app(app)

    # 只在第一次调用时创建表
    if not _tables_created:
        with app.app_context():
            db.create_all()
            print("[数据库] 表创建完成")
            _tables_created = True
