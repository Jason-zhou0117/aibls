from bilibili_api import Credential
from sqlalchemy import Column, String

from aibls.models.base import BaseModel


class LoginCookie(BaseModel):
    #表名
    __tablename__ = 'login_cookie'
    #字段
    login_id = Column(name="login_id", type_=String(50), primary_key=True, comment="登录ID")
    nick_name = Column(name="nick_name", type_=String(50), primary_key=False, comment="昵称")
    user_face = Column(name="user_face", type_=String(1000), primary_key=False, comment="头像")
    sess_data = Column(name="sess_data", type_=String(500), primary_key=False, comment="Session数据-Sess_Data")
    buvid3 = Column(name="buvid3", type_=String(100), primary_key=False, comment="buvid3")
    bili_jct = Column(name="bili_jct", type_=String(50), primary_key=False, comment="Bili_Jct")
    ac_time_value = Column(name="ac_time_value", type_=String(50), primary_key=False, comment="ac_time_value")
    dede_user_id = Column(name="dede_user_id", type_=String(50), primary_key=False, comment="Dede_User_ID")

    # 防止隐式I/O的配置
    __mapper_args__ = {
        "eager_defaults": True
    }

    def __repr__(self):
        return f"<LoginCookie(login_id={self.login_id}, nick_name='{self.nick_name}')>"

    def get_credential(self) -> Credential:
        """获取登录凭证"""
        return Credential(
            sessdata = self.get_sess_data(),
            bili_jct = self.get_bili_jct(),
            buvid3 = self.get_buvid3(),
            dedeuserid = self.get_dede_user_id(),
            ac_time_value = self.get_ac_time_value(),
        )

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
