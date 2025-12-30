from typing import List
from sqlalchemy.orm import Session
import sys
import os

# 修复相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 导入模型
from models import DeviceModel, SensorDataModel, MQTTConfigModel, TopicConfigModel
from database import SessionLocal


def get_device_by_id(db: Session, device_id: int):
    """根据ID获取设备"""
    return db.query(DeviceModel).filter(DeviceModel.id == device_id).first()


def get_device_by_name(db: Session, name: str):
    """根据名称获取设备"""
    return db.query(DeviceModel).filter(DeviceModel.name == name).first()


def get_devices(db: Session, skip: int = 0, limit: int = 100):
    """获取设备列表"""
    return db.query(DeviceModel).offset(skip).limit(limit).all()


def create_device(db: Session, device_data: dict):
    """创建设备"""
    db_device = DeviceModel(**device_data)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, device_id: int, device_data: dict):
    """更新设备"""
    db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
    if db_device:
        for key, value in device_data.items():
            setattr(db_device, key, value)
        db.commit()
        db.refresh(db_device)
    return db_device


def delete_device(db: Session, device_id: int):
    """删除设备"""
    db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False


def get_sensor_data_by_device(db: Session, device_id: int):
    """获取设备的传感器数据"""
    return db.query(SensorDataModel).filter(SensorDataModel.device_id == device_id).all()


def get_all_sensors_from_db(db: Session):
    """获取所有传感器数据"""
    return db.query(SensorDataModel).all()


def get_latest_sensors_from_db(db: Session):
    """获取每个传感器类型的最新数据"""
    # 获取所有唯一的传感器类型
    unique_sensor_types = db.query(SensorDataModel.type).distinct().all()
    
    latest_sensors = []
    
    for sensor_type, in unique_sensor_types:
        # 为每个传感器类型获取最新的记录
        latest_sensor = db.query(SensorDataModel).filter(
            SensorDataModel.type == sensor_type
        ).order_by(SensorDataModel.timestamp.desc()).first()
        
        if latest_sensor:
            latest_sensors.append(latest_sensor)
    
    return latest_sensors


def get_device_history_from_db(db: Session, device_id: int):
    """获取设备的历史传感器数据"""
    # 获取设备的传感器数据，按时间倒序排列，限制为最近100条
    return db.query(SensorDataModel).filter(
        SensorDataModel.device_id == device_id
    ).order_by(SensorDataModel.timestamp.desc()).limit(100).all()


def create_sensor_data(db: Session, sensor_data: dict):
    """创建传感器数据"""
    db_sensor = SensorDataModel(**sensor_data)
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


def get_mqtt_config_by_id(db: Session, config_id: int):
    """根据ID获取MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()


def get_mqtt_configs(db: Session, skip: int = 0, limit: int = 100):
    """获取MQTT配置列表"""
    return db.query(MQTTConfigModel).offset(skip).limit(limit).all()


def create_mqtt_config(db: Session, config_data: dict):
    """创建MQTT配置"""
    db_config = MQTTConfigModel(**config_data)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_mqtt_config(db: Session, config_id: int, config_data: dict):
    """更新MQTT配置"""
    db_config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if db_config:
        for key, value in config_data.items():
            setattr(db_config, key, value)
        db.commit()
        db.refresh(db_config)
    return db_config


def delete_mqtt_config(db: Session, config_id: int):
    """删除MQTT配置"""
    db_config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if db_config:
        db.delete(db_config)
        db.commit()
        return True
    return False


def get_topic_config_by_id(db: Session, config_id: int):
    """根据ID获取主题配置"""
    return db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()


def get_topic_configs(db: Session, skip: int = 0, limit: int = 100):
    """获取主题配置列表"""
    return db.query(TopicConfigModel).offset(skip).limit(limit).all()


def create_topic_config(db: Session, config_data: dict):
    """创建主题配置"""
    db_config = TopicConfigModel(**config_data)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_topic_config(db: Session, config_id: int, config_data: dict):
    """更新主题配置"""
    db_config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if db_config:
        for key, value in config_data.items():
            setattr(db_config, key, value)
        db.commit()
        db.refresh(db_config)
    return db_config


def delete_topic_config(db: Session, config_id: int):
    """删除主题配置"""
    db_config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if db_config:
        db.delete(db_config)
        db.commit()
        return True
    return False