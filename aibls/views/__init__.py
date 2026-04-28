


from flask import Blueprint


"""用户API的蓝图定义"""
user_api = Blueprint("user_api",__name__)
"""房间API的蓝图定义"""
room_api = Blueprint("room_api",__name__)
"""弹幕API的蓝图定义"""
live_api = Blueprint("live_api",__name__)
"""入场视频配置蓝图"""
vip_api = Blueprint("vip_api",__name__)


from aibls.views import login_route   # 导入登录路由
from aibls.views import room_route    # 导入房间路由
from aibls.views import live_route
from aibls.views import vip_config_route
