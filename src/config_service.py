from typing import List
from sqlalchemy.orm import Session
import sys
import os

# 修复相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 使用绝对路径导入模型
from src.models import DeviceModel, SensorDataModel, MQTTConfigModel, TopicConfigModel
from src.database import SessionLocal
from src.db_operations import get_active_topic_config  # 导入函数


def get_active_mqtt_config(db: Session):
    """获取激活的MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.is_active == True).first()