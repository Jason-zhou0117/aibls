from flask_sqlalchemy import SQLAlchemy

from aibls.config import get_app_settings


"""定义数据库对象"""
db = SQLAlchemy()

#读取配置文件
config = get_app_settings()



