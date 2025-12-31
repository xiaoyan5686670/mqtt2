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
    delete_topic_config, activate_topic_config
)

# MQTT数据处理相关代码
import paho.mqtt.client as mqtt
import re


class MQTTService:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.active_config = None
        self.topic_config = None

    def init_mqtt_client(self):
        """初始化MQTT客户端"""
        # 获取激活的MQTT配置
        db = SessionLocal()
        try:
            self.active_config = get_active_mqtt_config(db)
            self.topic_config = get_active_topic_config(db)
        finally:
            db.close()
        
        if not self.active_config:
            print("未找到激活的MQTT配置")
            return False
            
        if not self.topic_config:
            print("未找到激活的主题配置")
            return False
        
        # 创建MQTT客户端
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # 设置用户名密码（如果有的话）
        if self.active_config.username and self.active_config.password:
            self.client.username_pw_set(
                self.active_config.username, 
                self.active_config.password
            )
        
        # 连接MQTT服务器
        try:
            self.client.connect(
                self.active_config.server, 
                self.active_config.port, 
                60
            )
            return True
        except Exception as e:
            print(f"MQTT连接失败: {e}")
            return False

    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调函数"""
        if rc == 0:
            print("MQTT连接成功")
            self.is_connected = True
            
            # 解析订阅主题
            subscribe_topics_str = self.topic_config.subscribe_topics
            if subscribe_topics_str:
                try:
                    # 尝试解析为JSON数组
                    topics = json.loads(subscribe_topics_str)
                    if isinstance(topics, list):
                        for topic in topics:
                            client.subscribe(topic)
                            print(f"订阅主题: {topic}")
                    else:
                        # 如果不是列表，直接订阅
                        client.subscribe(subscribe_topics_str)
                        print(f"订阅主题: {subscribe_topics_str}")
                except json.JSONDecodeError:
                    # 如果不是JSON格式，则按换行符分割
                    topics = subscribe_topics_str.split('\n')
                    for topic in topics:
                        topic = topic.strip()
                        if topic:
                            client.subscribe(topic)
                            print(f"订阅主题: {topic}")
        else:
            print(f"MQTT连接失败，错误码: {rc}")
            self.is_connected = False

    def on_message(self, client, userdata, msg):
        """MQTT消息回调函数"""
        print(f"收到消息: {msg.topic} - {msg.payload.decode()}")
        
        try:
            # 解析传感器数据
            payload = msg.payload.decode()
            self.process_sensor_data(payload, msg.topic)
        except Exception as e:
            print(f"处理消息时出错: {e}")

    def process_sensor_data(self, payload, topic):
        """处理传感器数据"""
        # 解析传感器数据
        # 格式示例: "stm32/1 Temperature1: 22.10 C, Humidity1: 16.10 %\nTemperature2: 21.80 C, Humidity2: 23.40 %\nRelay Status: 1\nPB8 Level: 1"
        
        # 解析温度1和湿度1
        temp1_match = re.search(r'Temperature1:\s*([\d.]+)\s*C', payload)
        hum1_match = re.search(r'Humidity1:\s*([\d.]+)\s*%', payload)
        
        # 解析温度2和湿度2
        temp2_match = re.search(r'Temperature2:\s*([\d.]+)\s*C', payload)
        hum2_match = re.search(r'Humidity2:\s*([\d.]+)\s*%', payload)
        
        # 解析继电器状态
        relay_match = re.search(r'Relay Status:\s*(\d)', payload)
        
        # 解析PB8电平
        pb8_match = re.search(r'PB8 Level:\s*(\d)', payload)
        
        # 从主题中提取设备信息
        # 主题格式应为 "prefix/device_name"，例如 "stm32/1"
        parts = topic.split('/')
        if len(parts) < 2:
            print(f"主题格式不正确，跳过处理: {topic}")
            return
        
        device_name = parts[1]
        
        # 检查设备名称是否有效（避免只包含数字等无效名称）
        if not device_name or device_name.isdigit() or len(device_name) <= 1:
            print(f"设备名称无效，跳过创建设备: {device_name}")
            return
        
        db = SessionLocal()
        try:
            # 查找设备
            device = db.query(DeviceModel).filter(DeviceModel.name == device_name).first()
            if not device:
                print(f"设备 {device_name} 不存在，跳过处理")
                return  # 不再自动创建设备，需要用户手动创建
            
            # 保存传感器数据
            if temp1_match:
                self.save_sensor_data(db, device.id, "Temperature1", float(temp1_match.group(1)), "°C")
            if hum1_match:
                self.save_sensor_data(db, device.id, "Humidity1", float(hum1_match.group(1)), "%")
            if temp2_match:
                self.save_sensor_data(db, device.id, "Temperature2", float(temp2_match.group(1)), "°C")
            if hum2_match:
                self.save_sensor_data(db, device.id, "Humidity2", float(hum2_match.group(1)), "%")
            if relay_match:
                self.save_sensor_data(db, device.id, "Relay Status", int(relay_match.group(1)), "")
            if pb8_match:
                self.save_sensor_data(db, device.id, "PB8 Level", int(pb8_match.group(1)), "")
            
            db.commit()
        except Exception as e:
            print(f"保存传感器数据时出错: {e}")
            db.rollback()
        finally:
            db.close()

    def save_sensor_data(self, db, device_id, sensor_type, value, unit):
        """保存传感器数据到数据库"""
        # 检查是否已存在相同类型的传感器数据
        existing_sensor = db.query(SensorDataModel).filter(
            SensorDataModel.device_id == device_id,
            SensorDataModel.type == sensor_type
        ).first()
        
        if existing_sensor:
            # 更新现有传感器数据
            existing_sensor.value = value
            existing_sensor.unit = unit
            existing_sensor.timestamp = datetime.utcnow()
        else:
            # 创建新的传感器数据
            sensor_data = SensorDataModel(
                device_id=device_id,
                type=sensor_type,
                value=value,
                unit=unit,
                timestamp=datetime.utcnow(),
                min_value=0,
                max_value=100,
                alert_status="normal"
            )
            db.add(sensor_data)

    def start(self):
        """启动MQTT客户端"""
        if not self.client:
            if not self.init_mqtt_client():
                return False
        
        # 在单独的线程中启动MQTT客户端循环
        self.client.loop_start()
        return True

    def stop(self):
        """停止MQTT客户端"""
        if self.client:
            self.client.loop_stop()
            self.is_connected = False


# 创建全局MQTT服务实例
mqtt_service = MQTTService()


def start_mqtt_service():
    """启动MQTT服务"""
    return mqtt_service.start()


# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI()

# 添加CORS中间件 - 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法，包括GET, POST, PUT, DELETE, OPTIONS等
    allow_headers=["*"],  # 允许所有请求头
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
async def update_device_api(device_id: int, device: Device, db: Session = Depends(get_db_session)):
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
        result.append({
            "topic": msg.topic or "unknown",
            "payload": msg.value,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
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


