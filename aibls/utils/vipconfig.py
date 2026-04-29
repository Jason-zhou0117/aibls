import json
import logging
import os
from typing import Optional, Dict, Any

from settings import APP_ROOT, VIDEO_DIR, CONFIG_DIR

logger = logging.getLogger(__name__)

class VIPConfig:
    # 静态变量 - JSON对象
    _vip_users: Optional[Dict[str, Any]] = None
    _file_path: str = "vip_users.json"  # 默认文件路径

    @classmethod
    def __get_file_path(cls) -> str:
        # 应用根目录
        file_path = os.path.join(CONFIG_DIR, cls._file_path)
        return file_path


    @classmethod
    def load_json(cls) -> Dict[str, Any]:
        """
        静态方法：如果初始变量为空，则从文件中读取JSON串转换为JSON对象
        Returns:
            JSON对象（字典）
        """

        file_path = cls.__get_file_path()
        # 如果变量为空，从文件加载
        if cls._vip_users is None:
            try:
                logger.info(f"获取VIP用户配置文件路径: {file_path}")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cls._vip_users = json.load(f)
                    logger.info(f"成功从文件加载JSON: {cls._vip_users}")
                else:
                    # 文件不存在，创建空字典
                    cls._vip_users = {"items":[]}
                    logger.info(f"文件不存在，创建空JSON对象: {file_path}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                cls._vip_users =  {"items":[]}
            except Exception as e:
                logger.error(f"读取文件错误: {e}")
                cls._vip_users =  {"items":[]}

        return cls._vip_users

    @classmethod
    def save_to_file(cls) -> bool:
        """
        将当前JSON对象写入文件
        """
        try:
            save_path = cls.__get_file_path()

            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(cls._vip_users, f, ensure_ascii=False, indent=2)

            logger.info(f"成功保存JSON到文件: {save_path}")
            return True

        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return False

    @classmethod
    def add_user_config(cls, user_config:Any):
        try:
            if cls._vip_users is None:
                cls.load_json()

            userid = user_config["userid"]
            cls._vip_users[userid] = user_config
            cls.save_to_file()
        except Exception as e:
            logger.error(f"添加VIP视频配置失败: {e}")
            raise e

    @classmethod
    def update_user_config(cls, target_id,user_config: Any):
        try:
            if cls._vip_users is None:
                cls.load_json()
            if target_id in cls._vip_users:
                user_data = cls._vip_users[target_id]
                user_data["name"] =  user_config["name"]
                user_data["nickname"] =  user_config["nickname"]
                user_data["face"] =  user_config["face"]
                cls._vip_users[target_id] = user_config
                cls.save_to_file()
        except Exception as e:
            logger.error(f"添加VIP视频配置失败: {e}")
            raise e

    @classmethod
    def clear(cls, save_to_file: bool = True) -> None:
        """清空所有数据"""
        cls._vip_users = {"items":[]}
        if save_to_file:
            cls.save_to_file()
        print("已清空所有数据")

    @classmethod
    def reload(cls) -> Dict[str, Any]:
        """重新加载JSON文件"""
        cls._vip_users = None
        return cls.load_json()

    @classmethod
    def config_to_list(cls):
        """将字典格式转换为列表格式（用于前端展示）"""
        items = []
        config_dict_data = cls.load_json()
        for uid, user_data in config_dict_data.items():
            items.append({
                'userid': uid,
                'name': user_data.get('name', ''),
                'nickname': user_data.get('nickname', ''),
                'face': user_data.get('face', ''),
                'videos': user_data.get('videos', []),
                'created_at': user_data.get('created_at', '')
            })
        return items

    @classmethod
    def remove_user(cls,uid:str):
        json_data = cls.load_json()

        if uid in json_data:
            # 可选：删除用户关联的视频文件
            user_data = json_data[uid]
            for video in user_data.get('videos', []):
                video_path = video.get('path')
                if video_path and os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                    except Exception as e:
                        logger.error(f"删除视频文件失败: {e}")

            del json_data[uid]
            cls.save_to_file()

    @classmethod
    def add_video(cls, vip_user_id:str,video_item:Any):
        try:
            if cls._vip_users is None:
                cls.load_json()
            if vip_user_id not in cls._vip_users:
                raise BaseException(-30001,f"用户ID:{vip_user_id}不存在")
            cls._vip_users[vip_user_id].setdefault('videos', []).append(video_item)
            cls.save_to_file()
        except Exception as e:
            logger.error(f"添加VIP视频文件失败: {e}")
            raise e

    @classmethod
    def delete_video(cls, video_id: str):
        try:
            if cls._vip_users is None:
                cls.load_json()

            for uid, user_data in cls._vip_users.items():
                videos = user_data.get('videos', [])
                for i, video in enumerate(videos):
                    if video.get('id') == video_id:
                        # 删除视频文件
                        video_path = video.get('path')
                        if video_path and os.path.exists(video_path):
                            try:
                                os.remove(video_path)
                            except Exception as e:
                                logger.error(f"删除视频文件失败: {e}")

                        del cls._vip_users[uid]['videos'][i]
                        cls.save_to_file()
        except Exception as e:
            logger.error(f"删除VIP视频文件失败: {e}")

    @classmethod
    def get_video_path(cls, filename: str) -> str:
        # 应用根目录
        folder_path = VIDEO_DIR
        # 如果目录不存在，则生成目录
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, filename)
        return file_path