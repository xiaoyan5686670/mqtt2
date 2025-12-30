import sys
import os

# 修复相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from models import MQTTConfigModel, TopicConfigModel
from sqlalchemy.orm import Session


def get_active_mqtt_config(db: Session):
    """获取激活的MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.is_active == True).first()


def get_active_topic_config(db: Session):
    """获取激活的主题配置"""
    return db.query(TopicConfigModel).filter(TopicConfigModel.is_active == True).first()