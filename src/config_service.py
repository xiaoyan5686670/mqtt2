from sqlalchemy.orm import Session
from .models import MQTTConfigModel, TopicConfigModel


def get_active_mqtt_config(db: Session):
    """获取激活的MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.is_active == True).first()


def get_active_topic_config(db: Session):
    """获取激活的主题配置"""
    return db.query(TopicConfigModel).filter(TopicConfigModel.is_active == True).first()