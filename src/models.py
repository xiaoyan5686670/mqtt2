import sys
import os
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# 动态添加父目录到模块搜索路径，以便导入database
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.database import Base


class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    device_type = Column(String)
    status = Column(String, default="offline")
    location = Column(String, nullable=True)
    mqtt_config_id = Column(Integer, nullable=True)  # 关联的MQTT配置ID
    topic_config_id = Column(Integer, nullable=True)  # 关联的主题配置ID


class SensorDataModel(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer)
    type = Column(String)
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime)
    min_value = Column(Float)
    max_value = Column(Float)
    alert_status = Column(String)


class MQTTConfigModel(Base):
    __tablename__ = "mqtt_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    server = Column(String)
    port = Column(Integer)
    username = Column(String)
    password = Column(String)
    is_active = Column(Boolean, default=False)


class TopicConfigModel(Base):
    __tablename__ = "topic_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    subscribe_topics = Column(String)  # JSON格式的订阅主题列表
    publish_topic = Column(String)
    is_active = Column(Boolean, default=False)
    mqtt_config_id = Column(Integer, nullable=True)  # 关联的MQTT配置ID


# Pydantic模型定义
class DeviceBase(BaseModel):
    name: str
    device_type: str
    location: Optional[str] = None


class DeviceCreate(DeviceBase):
    mqtt_config_id: Optional[int] = None
    topic_config_id: Optional[int] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    mqtt_config_id: Optional[int] = None
    topic_config_id: Optional[int] = None


class Device(DeviceBase):
    id: int
    status: str
    mqtt_config_id: Optional[int] = None
    topic_config_id: Optional[int] = None

    class Config:
        from_attributes = True


class SensorDataBase(BaseModel):
    device_id: int
    type: str
    value: float
    unit: str


class SensorDataCreate(SensorDataBase):
    pass


class SensorData(SensorDataBase):
    id: int
    timestamp: datetime
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    alert_status: Optional[str] = None

    class Config:
        from_attributes = True


class MQTTConfigBase(BaseModel):
    name: str
    server: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None


class MQTTConfigCreate(MQTTConfigBase):
    pass


class MQTTConfigUpdate(BaseModel):
    name: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class MQTTConfig(MQTTConfigBase):
    id: int
    is_active: bool = False

    class Config:
        from_attributes = True


class TopicConfigBase(BaseModel):
    name: str
    subscribe_topics: str
    publish_topic: Optional[str] = None


class TopicConfigCreate(TopicConfigBase):
    pass


class TopicConfigUpdate(BaseModel):
    name: Optional[str] = None
    subscribe_topics: Optional[str] = None
    publish_topic: Optional[str] = None
    is_active: Optional[bool] = None


class TopicConfig(TopicConfigBase):
    id: int
    is_active: bool = False

    class Config:
        from_attributes = True