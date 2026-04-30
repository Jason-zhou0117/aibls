# aibls/scripts/migrate_json_to_db.py
import json
import os
import uuid
from pathlib import Path
from aibls.models.database import db, VIPUser, UserVideo
from aibls.services.vip_service import vip_service


def migrate_json_to_db(json_path=None):
    """将旧的JSON配置迁移到数据库"""
    if not json_path:
        json_path = Path(__file__).parent.parent.parent / 'config' / 'vip_users.json'

    print(f"JSON文件: {json_path}")

    if not json_path.exists():
        print(f"JSON文件不存在: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # config 是 {uid: user_data} 格式
    for uid, user_data in config.items():
        # 添加用户
        user, error = vip_service.add_user(
            uid=uid,
            name=user_data.get('name', ''),
            nickname=user_data.get('nickname', ''),
            face=user_data.get('face', '')
        )

        if error:
            print(f"迁移用户 {uid} 失败: {error}")
            continue

        print(f"迁移用户: {user_data.get('name')} ({uid})")

        # 迁移视频
        for video_data in user_data.get('videos', []):
            video_id = str(uuid.uuid4())[:8]
            video, error = vip_service.add_video(
                uid=uid,
                video_id=video_id,
                title=video_data.get('title', ''),
                url=video_data.get('url', ''),
                path=video_data.get('path', '')
            )
            if error:
                print(f"  迁移视频失败: {error}")
            else:
                print(f"  迁移视频: {video_data.get('title')}")

    # try:
    #     os.remove(json_path)
    # except Exception as e:
    #     print(f"删除视频文件失败: {e}")

    print("迁移完成！")