from sqlalchemy import Column, DateTime, func


from aibls import db


class BaseModel(db.Model):
    """抽象基类，包含通用字段和方法"""
    __abstract__ = True

    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    def to_dict(self):
        """将模型对象转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            result[column.name] = value
        return result

    @classmethod
    def from_dict(cls, data):
        """从字典创建模型对象"""
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance

    def update_from_dict(self, data):
        """从字典更新模型对象"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['created_at']:
                setattr(self, key, value)

