import asyncio
import logging
from typing import Any

from bilibili_api import Credential, user
from bilibili_api.user import User

from aibls.daos.user_dao import UserDAO
from aibls.exceptions.BLSException import BLSException
from aibls.models.users import LoginCookie

logger = logging.getLogger(__name__)

class UserService:

    def __init__(self):
        self.user_dao = UserDAO()

    def get_live_user(self,user_id:int,login_user_credential:Credential) -> dict:
        try:
            # 根据房间号，获取房主的用户信息
            user_obj = user.User(user_id, credential=login_user_credential)
            user_info: dict[str, Any] = asyncio.run(user_obj.get_user_info())
            return user_info
        except Exception as e:
            logger.error(f"实时获取用户信息时出错：{e}")
            raise BLSException(-10001, "实时获取用户信息时出错")

    def save_login_user(self,credential: Credential) -> dict[str,Any]:
        """
        保存登录用户信
        :param credential: 扫二维码后的登录凭证
        :return: 登录用户信息
        """

        logger.info("登录用户的凭据：UID={},AC_TIME_VALUE={}"
                    .format(credential.dedeuserid, credential.ac_time_value))
        # 获取Bili用户对象
        bili_user: User = user.User(credential.dedeuserid, credential)
        # 获取Bili用户信息
        bili_user_info: dict = asyncio.run(bili_user.get_user_info())
        print("登录后的用户信息：")
        print(bili_user_info)
        logger.info("获取客户的登录信息：UID={},昵称={}"
                    .format(bili_user.get_uid(), bili_user_info["name"]))
        dict_user = {
            "login_id": bili_user.get_uid(),
            "nick_name":bili_user_info["name"],
            "user_face": bili_user_info["face"],
            "sess_data": credential.sessdata,
            "buvid3": credential.buvid3,
            "bili_jct": credential.bili_jct,
            "ac_time_value": credential.ac_time_value,
            "dede_user_id": credential.dedeuserid,
        }
        # 保存登录并获取登录对象
        login_user: LoginCookie = self.user_dao.save(str(bili_user.get_uid()),dict_user)
        return login_user.to_dict()