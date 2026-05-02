
import os

from aibls.settings import VIDEO_DIR


class VIPConfig:


    @classmethod
    def get_video_path(cls, filename: str) -> str:
        # 应用根目录
        folder_path = VIDEO_DIR
        # 如果目录不存在，则生成目录
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, filename)
        return file_path