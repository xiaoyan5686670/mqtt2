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


def get_device_by_id(db: Session, device_id: int):
    """根据ID获取设备"""
    return db.query(DeviceModel).filter(DeviceModel.id == device_id).first()


def get_device(db: Session, device_id: int):
    """根据ID获取设备（与get_device_by_id功能相同，保持兼容性）"""
    return db.query(DeviceModel).filter(DeviceModel.id == device_id).first()


def get_device_by_name(db: Session, name: str):
    """根据名称获取设备"""
    return db.query(DeviceModel).filter(DeviceModel.name == name).first()


def get_devices(db: Session, skip: int = 0, limit: int = 100):
    """获取设备列表"""
    return db.query(DeviceModel).offset(skip).limit(limit).all()


def create_device(db: Session, device_data):
    """创建设备"""
    # 如果传入的是Pydantic模型，转换为字典
    if hasattr(device_data, 'dict'):
        device_dict = device_data.dict()
    else:
        device_dict = device_data
    
    db_device = DeviceModel(**device_dict)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, device_id: int, device_data):
    """更新设备"""
    # 如果传入的是Pydantic模型，转换为字典
    if hasattr(device_data, 'dict'):
        device_dict = device_data.dict()
    else:
        device_dict = device_data
    
    db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
    if db_device:
        for key, value in device_dict.items():
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


def get_active_topic_config(db: Session):
    """获取激活的主题配置"""
    return db.query(TopicConfigModel).filter(TopicConfigModel.is_active == True).first()


def get_mqtt_configs(db: Session, skip: int = 0, limit: int = 100):
    """获取MQTT配置列表"""
    return db.query(MQTTConfigModel).offset(skip).limit(limit).all()


def create_mqtt_config(db: Session, config_data):
    """创建MQTT配置"""
    # 如果传入的是Pydantic模型，转换为字典
    if hasattr(config_data, 'dict'):
        config_dict = config_data.dict()
    else:
        config_dict = config_data
    
    db_config = MQTTConfigModel(**config_dict)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_mqtt_config(db: Session, config_id: int, config_data):
    """更新MQTT配置"""
    # 如果传入的是Pydantic模型，转换为字典
    if hasattr(config_data, 'dict'):
        config_dict = config_data.dict()
    else:
        config_dict = config_data
    
    db_config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if db_config:
        for key, value in config_dict.items():
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


def create_topic_config(db: Session, config_data):
    """创建主题配置"""
    # 如果传入的是Pydantic模型，转换为字典
    if hasattr(config_data, 'dict'):
        config_dict = config_data.dict()
    else:
        config_dict = config_data
    
    db_config = TopicConfigModel(**config_dict)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_topic_config(db: Session, config_id: int, config_data):
    """更新主题配置"""
    # 如果传入的是Pydantic模型，转换为字典
    if hasattr(config_data, 'dict'):
        config_dict = config_data.dict()
    else:
        config_dict = config_data
    
    db_config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if db_config:
        for key, value in config_dict.items():
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


def get_device_history(db: Session, device_id: int):
    """获取设备历史数据"""
    return db.query(SensorDataModel).filter(SensorDataModel.device_id == device_id).all()


def get_latest_device_sensors(db: Session, device_id: int):
    """获取指定设备的最新传感器数据"""
    from sqlalchemy import desc
    
    # 获取指定设备的所有传感器数据，按时间戳降序排列
    all_sensors = db.query(SensorDataModel).filter(
        SensorDataModel.device_id == device_id
    ).order_by(desc(SensorDataModel.timestamp)).all()
    
    # 按传感器类型分组，只保留每种类型最新的数据
    latest_sensors = {}
    for sensor in all_sensors:
        sensor_type = sensor.type
        if sensor_type not in latest_sensors:
            latest_sensors[sensor_type] = sensor
    
    # 返回最新的传感器数据列表
    return list(latest_sensors.values())


def get_device_sensors(db: Session, device_id: int):
    """获取设备传感器数据"""
    return db.query(SensorDataModel).filter(SensorDataModel.device_id == device_id).all()


def get_realtime_sensors(db: Session):
    """获取实时传感器数据"""
    from sqlalchemy import desc
    # 获取每个设备的最新传感器数据
    subquery = db.query(
        SensorDataModel.device_id,
        db.query(SensorDataModel).filter(
            SensorDataModel.device_id == SensorDataModel.device_id
        ).order_by(desc(SensorDataModel.timestamp)).limit(1).subquery()
    ).distinct(SensorDataModel.device_id).subquery()
    
    return db.query(SensorDataModel).join(
        subquery, SensorDataModel.id == subquery.c.id
    ).all()


def get_latest_sensors(db: Session):
    """获取最新传感器数据，按设备分组"""
    from sqlalchemy import desc
    # 获取最新的传感器数据
    sensors = db.query(SensorDataModel).order_by(desc(SensorDataModel.timestamp)).limit(50).all()
    
    # 按设备ID分组
    devices = {}
    for sensor in sensors:
        device_id = sensor.device_id
        if device_id not in devices:
            devices[device_id] = {
                'device_id': device_id,
                'sensors': []
            }
        # 添加传感器数据
        devices[device_id]['sensors'].append({
            'id': sensor.id,
            'type': sensor.type,
            'value': sensor.value,
            'unit': sensor.unit,
            'timestamp': sensor.timestamp
        })
    
    # 返回设备列表
    return list(devices.values())


def activate_mqtt_config(db: Session, config_id: int):
    """激活MQTT配置"""
    # 先将所有配置设为非激活
    db.query(MQTTConfigModel).update({MQTTConfigModel.is_active: False})
    # 激活指定配置
    config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if config:
        config.is_active = True
        db.commit()
        return True
    return False


def activate_topic_config(db: Session, config_id: int):
    """激活主题配置"""
    # 先将所有配置设为非激活
    db.query(TopicConfigModel).update({TopicConfigModel.is_active: False})
    # 激活指定配置
    config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if config:
        config.is_active = True
        db.commit()
        return True
    return False


def get_mqtt_config_by_id(db: Session, config_id: int):
    """根据ID获取MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()


def get_active_mqtt_config(db: Session):
    """获取激活的MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.is_active == True).first()


def update_topic_config(db: Session, config_id: int, config_data: dict):
    """更新主题配置"""
    db_config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if db_config:
        for key, value in config_data.items():
            setattr(db_config, key, value)
        db.commit()
        db.refresh(db_config)
    return db_config
