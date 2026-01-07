import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, desc
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from datetime import datetime
from contextlib import contextmanager

from fastapi import BackgroundTasks

# 导入CORS中间件
from fastapi.middleware.cors import CORSMiddleware

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./mqtt_iot.db"

# 创建引擎
from sqlalchemy import create_engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # 仅用于SQLite
)

# 创建会话工厂
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()


def get_db_session():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 数据模型定义
from src.models import DeviceModel, SensorDataModel, MQTTConfigModel, TopicConfigModel

# MQTT服务定义
from src.mqtt_service import mqtt_service

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
    mqtt_config_id: Optional[int] = None


class TopicConfigCreate(TopicConfigBase):
    pass


class TopicConfigUpdate(BaseModel):
    name: Optional[str] = None
    subscribe_topics: Optional[str] = None
    publish_topic: Optional[str] = None
    mqtt_config_id: Optional[int] = None
    is_active: Optional[bool] = None


class TopicConfig(TopicConfigBase):
    id: int
    is_active: bool = False

    class Config:
        from_attributes = True


# 导入数据库操作函数
from src.db_operations import (
    get_devices, get_device, create_device, update_device, delete_device, 
    get_device_history, get_device_sensors, get_realtime_sensors, get_latest_sensors,
    get_mqtt_configs, get_mqtt_config_by_id, create_mqtt_config, update_mqtt_config,
    delete_mqtt_config, activate_mqtt_config, get_active_topic_config, get_active_mqtt_config,  # 添加导入
    get_topic_configs, get_topic_config_by_id, create_topic_config, update_topic_config,
    delete_topic_config, activate_topic_config, get_latest_device_sensors, fix_device_status_null_values
)

# MQTT数据处理相关代码
import paho.mqtt.client as mqtt
import re

# 从外部导入MQTT服务
from src.mqtt_service import mqtt_service, get_active_mqtt_config, get_active_topic_config


def start_mqtt_service():
    """启动MQTT服务"""
    return mqtt_service.start()


# 创建数据库表
Base.metadata.create_all(bind=engine)

# 修复数据库中可能存在的NULL状态值
with SessionLocal() as db:
    fix_device_status_null_values(db)

# 创建FastAPI应用
app = FastAPI()

# 添加CORS中间件 - 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],  # 允许前端开发服务器
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法，包括GET, POST, PUT, DELETE, OPTIONS等
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],  # 明确指定允许的请求头，避免使用通配符与凭证冲突
)

# 获取当前文件所在目录的路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 使用绝对路径挂载静态文件目录
static_dir = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/api/devices", response_model=List[Device])
async def get_devices_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    devices = get_devices(db, skip=skip, limit=limit)
    return devices


@app.get("/api/devices/{device_id}", response_model=Device)
async def get_device_api(device_id: int, db: Session = Depends(get_db_session)):
    device = get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.post("/api/devices", response_model=Device)
async def create_device_api(device: DeviceCreate, db: Session = Depends(get_db_session)):
    db_device = create_device(db, device)
    return db_device


@app.put("/api/devices/{device_id}", response_model=Device)
async def update_device_api(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db_session)):
    db_device = update_device(db, device_id, device)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device


@app.delete("/api/devices/{device_id}")
async def delete_device_api(device_id: int, db: Session = Depends(get_db_session)):
    success = delete_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deleted successfully"}


@app.get("/api/devices/{device_id}/latest-sensors", response_model=List[SensorData])
async def get_latest_device_sensors_api(device_id: int, db: Session = Depends(get_db_session)):
    sensors = get_latest_device_sensors(db, device_id)
    return sensors


@app.get("/api/devices/{device_id}/history", response_model=List[dict])
async def get_device_history_api(device_id: int, db: Session = Depends(get_db_session)):
    history = get_device_history(db, device_id)
    return history


@app.get("/api/devices/{device_id}/sensors", response_model=List[SensorData])
async def get_device_sensors_api(device_id: int, db: Session = Depends(get_db_session)):
    sensors = get_device_sensors(db, device_id)
    return sensors


@app.get("/api/realtime-sensors")
async def get_realtime_sensors_api(db: Session = Depends(get_db_session)):
    sensors = get_realtime_sensors(db)
    return sensors


@app.get("/api/latest-sensors")
async def get_latest_sensors_api(db: Session = Depends(get_db_session)):
    sensors = get_latest_sensors(db)
    return sensors


# MQTT配置相关API
@app.get("/api/mqtt-configs", response_model=List[MQTTConfig])
async def get_mqtt_configs_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    configs = get_mqtt_configs(db, skip=skip, limit=limit)
    return configs


@app.get("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def get_mqtt_config_api(config_id: int, db: Session = Depends(get_db_session)):
    config = get_mqtt_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return config


@app.post("/api/mqtt-configs", response_model=MQTTConfig)
async def create_mqtt_config_api(config: MQTTConfigCreate, db: Session = Depends(get_db_session)):
    db_config = create_mqtt_config(db, config)
    return db_config


@app.put("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def update_mqtt_config_api(config_id: int, config: MQTTConfigUpdate, db: Session = Depends(get_db_session)):
    db_config = update_mqtt_config(db, config_id, config)
    if not db_config:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return db_config


@app.delete("/api/mqtt-configs/{config_id}")
async def delete_mqtt_config_api(config_id: int, db: Session = Depends(get_db_session)):
    success = delete_mqtt_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return {"message": "MQTT Config deleted successfully"}


# 激活MQTT配置API
@app.post("/api/mqtt-configs/{config_id}/activate")
async def activate_mqtt_config_api(config_id: int, db: Session = Depends(get_db_session)):
    success = activate_mqtt_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return {"message": "MQTT Config activated successfully"}


# 测试MQTT连接API
@app.post("/api/mqtt-configs/{config_id}/test")
async def test_mqtt_connection_api(config_id: int, db: Session = Depends(get_db_session)):
    config = get_mqtt_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    
    # 这里可以添加测试连接的逻辑
    return {"message": f"Testing connection for config {config.name}"}


# 主题配置相关API
@app.get("/api/topic-configs", response_model=List[TopicConfig])
async def get_topic_configs_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    configs = get_topic_configs(db, skip=skip, limit=limit)
    return configs


@app.get("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def get_topic_config_api(config_id: int, db: Session = Depends(get_db_session)):
    config = get_topic_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return config


@app.post("/api/topic-configs", response_model=TopicConfig)
async def create_topic_config_api(config: TopicConfigCreate, db: Session = Depends(get_db_session)):
    db_config = create_topic_config(db, config)
    return db_config


@app.put("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def update_topic_config_api(config_id: int, config: TopicConfigUpdate, db: Session = Depends(get_db_session)):
    db_config = update_topic_config(db, config_id, config)
    if not db_config:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return db_config


@app.delete("/api/topic-configs/{config_id}")
async def delete_topic_config_api(config_id: int, db: Session = Depends(get_db_session)):
    success = delete_topic_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return {"message": "Topic Config deleted successfully"}


# 添加激活配置和测试连接API
@app.post("/api/topic-configs/{config_id}/activate")
async def activate_topic_config_api(config_id: int, db: Session = Depends(get_db_session)):
    success = activate_topic_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return {"message": "Topic Config activated successfully"}


# MQTT消费相关的API端点
@app.post("/api/subscribe-topic")
async def subscribe_to_topic(
    topic: str = Body(..., embed=True),
    mqtt_config_id: int = Body(..., embed=True),
    db: Session = Depends(get_db_session)
):
    """
    订阅指定的MQTT主题
    """
    # 获取MQTT配置
    mqtt_config = get_mqtt_config_by_id(db, mqtt_config_id)
    if not mqtt_config:
        raise HTTPException(status_code=404, detail="MQTT配置不存在")
    
    # 更新全局MQTT服务的订阅主题
    global mqtt_service
    if mqtt_service and mqtt_service.client:
        # 使用MQTT服务的动态订阅功能
        mqtt_service.subscribe_to_topic(topic)
        return {"message": f"成功订阅主题: {topic}", "topic": topic}
    
    raise HTTPException(status_code=500, detail="MQTT服务未启动")


@app.post("/api/unsubscribe-topic")
async def unsubscribe_from_topic(
    topic: str = Body(..., embed=True),
    db: Session = Depends(get_db_session)
):
    """
    取消订阅指定的MQTT主题
    """
    global mqtt_service
    if mqtt_service and mqtt_service.client:
        mqtt_service.unsubscribe_from_topic(topic)
        return {"message": f"成功取消订阅主题: {topic}", "topic": topic}
    
    raise HTTPException(status_code=500, detail="MQTT服务未启动")


# 用于获取实时MQTT消息的API
@app.get("/api/mqtt-messages")
async def get_mqtt_messages(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db_session)
):
    """
    获取最近的MQTT消息
    """
    # 从传感器数据表获取最近的消息
    messages = db.query(SensorDataModel).order_by(desc(SensorDataModel.timestamp)).offset(skip).limit(limit).all()
    
    # 转换为合适的格式
    result = []
    for msg in messages:
        # 获取关联的设备信息
        device = db.query(DeviceModel).filter(DeviceModel.id == msg.device_id).first()
        device_name = device.name if device else "Unknown Device"
        
        result.append({
            "topic": f"device/{device_name}/{msg.type}" if device else f"sensor/{msg.id}",
            "payload": msg.value,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
            "device_name": device_name,
            "sensor_type": msg.type
        })
    
    return result


# 主页面路由 - 提供前端应用
@app.get("/")
async def read_root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MQTT IoT 管理系统</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    </head>
    <body>
        <div id="app"></div>
        <script type="module" src="/static/js/app.js"></script>
    </body>
    </html>
    """)

# 为前端路由提供fallback，确保SPA路由正常工作
# 必须在所有具体路由之后定义
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MQTT IoT 管理系统</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    </head>
    <body>
        <div id="app"></div>
        <script type="module" src="/static/js/app.js"></script>
    </body>
    </html>
    """)

# 执行数据库迁移
def migrate_database():
    # 检查是否已存在表，如果不存在则创建
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # 如果设备表不存在，则创建默认数据
    if "devices" not in existing_tables:
        print("初始化数据库...")
        # 这里可以添加创建默认数据的逻辑
    else:
        print("数据库已存在，跳过初始化")
        
        # 检查是否有设备数据，如果没有则不添加默认设备（保持用户数据）
        db = SessionLocal()
        try:
            device_count = db.query(DeviceModel).count()
            if device_count == 0:
                print("数据库中没有设备")
            else:
                print(f"数据库中已有 {device_count} 个设备")
        except Exception as e:
            print(f"检查设备数据时出错: {e}")
        finally:
            db.close()


# 启动时执行数据库迁移
migrate_database()


# 启动时启动MQTT服务
try:
    start_mqtt_service()
    print("MQTT服务启动成功")
except Exception as e:
    print(f"启动MQTT服务失败: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


