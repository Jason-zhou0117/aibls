# dao/base_dao.py
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic

from aibls import db

T = TypeVar('T')


class BaseDAO(Generic[T]):
    """基础数据访问对象类"""

    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
        self.db = db
        self.session = db.session

    def create(self, **kwargs) -> T:
        """创建记录"""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.commit()
        return instance

    def create_from_dict(self, data: Dict[str, Any]) -> T:
        """从字典创建记录"""
        instance = self.model_class.from_dict(data)
        self.session.add(instance)
        self.session.commit()
        return instance

    def get_by_id(self, id: str) -> Optional[T]:
        """根据ID获取记录"""
        return self.session.query(self.model_class).get(id)

    def get_all(self) -> List[T]:
        """获取所有记录"""
        return self.session.query(self.model_class).all()

    def update(self, id: str, **kwargs) -> Optional[T]:
        """更新记录"""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.commit()
        return instance

    def save(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """更新记录"""
        instance = self.get_by_id(id)
        if instance:
            instance.update_from_dict(data)
            self.session.commit()
        else:
            instance = self.create_from_dict(data)
        return instance

    def delete(self, id: str) -> bool:
        """删除记录"""
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False

    def find_by(self, **kwargs) -> List[T]:
        """根据条件查找记录"""
        query = self.session.query(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.all()

    def find_by_dict(self, filters:dict[str,Any]) -> List[T]:
        """根据条件查找记录"""
        query = self.session.query(self.model_class)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
        return query.all()

    def find_one_by(self, **kwargs) -> Optional[T]:
        """根据条件查找单条记录"""
        query = self.session.query(self.model_class)
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.first()

    def paginate(self, page: int = 1, per_page: int = 10, **filters) -> Dict[str, Any]:
        """分页查询"""
        query = self.session.query(self.model_class)

        # 应用过滤器
        for key, value in filters.items():
            if value is not None and hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)

        # 计算总数
        total = query.count()

        # 分页
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }

    def count(self, **filters) -> int:
        """统计记录数"""
        query = self.session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.count()