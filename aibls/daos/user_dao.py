from typing import Optional, Any

from aibls.daos.base_dao import BaseDAO
from aibls.models.users import LoginCookie


class UserDAO(BaseDAO[LoginCookie]):
    """登录用户数据访问对象"""

    def __init__(self):
        super().__init__(LoginCookie)




