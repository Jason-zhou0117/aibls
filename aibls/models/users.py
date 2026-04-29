from bilibili_api import Credential



class LoginCookie:

    @classmethod
    def dic_to_credential(cls,data: dict) -> Credential:
        """获取登录凭证"""
        return Credential(
            sessdata = data["sess_data"],
            bili_jct = data["bili_jct"],
            buvid3 = data["buvid3"],
            dedeuserid = data["dede_user_id"],
            ac_time_value = data["ac_time_value"],
        )
