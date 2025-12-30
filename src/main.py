import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from datetime import datetime
from contextlib import contextmanager

from fastapi import BackgroundTasks

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


@contextmanager
def get_db_session():
    """数据库会话上下文管理器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 数据模型定义
class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    device_type = Column(String)
    status = Column(String, default="离线")
    location = Column(String)
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


# 数据库操作函数
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


def get_active_mqtt_config(db: Session):
    """获取激活的MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.is_active == True).first()


def get_active_topic_config(db: Session):
    """获取激活的主题配置"""
    return db.query(TopicConfigModel).filter(TopicConfigModel.is_active == True).first()


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
        
        # 创建设备（如果不存在）
        device_name = topic.split('/')[1] if '/' in topic else topic
        db = SessionLocal()
        try:
            # 查找或创建设备
            device = db.query(DeviceModel).filter(DeviceModel.name == device_name).first()
            if not device:
                device = DeviceModel(
                    name=device_name,
                    device_type="STM32传感器",
                    status="在线",
                    location="未知位置"
                )
                db.add(device)
                db.commit()
                db.refresh(device)
            
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

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="src/static"), name="static")


# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# API路由定义
@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/api/devices", response_model=List[Device])
async def get_devices_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    devices = get_devices(db, skip=skip, limit=limit)
    return devices


@app.get("/api/devices/{device_id}", response_model=Device)
async def get_device_api(device_id: int, db: Session = Depends(get_db)):
    device = get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.post("/api/devices", response_model=Device)
async def create_device_api(device: Device, db: Session = Depends(get_db)):
    db_device = get_device_by_name(db, device.name)
    if db_device:
        raise HTTPException(status_code=400, detail="Device already exists")
    device_data = device.model_dump()
    result = create_device(db, device_data)
    return result


@app.put("/api/devices/{device_id}", response_model=Device)
async def update_device_api(device_id: int, device: Device, db: Session = Depends(get_db)):
    device_data = device.model_dump()
    result = update_device(db, device_id, device_data)
    if not result:
        raise HTTPException(status_code=404, detail="Device not found")
    return result


@app.delete("/api/devices/{device_id}")
async def delete_device_api(device_id: int, db: Session = Depends(get_db)):
    success = delete_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deleted successfully"}


@app.get("/api/devices/{device_id}/history", response_model=List[dict])
async def get_device_history_api(device_id: int, db: Session = Depends(get_db)):
    history = get_device_history_from_db(db, device_id)
    # 将SQLAlchemy模型转换为字典
    return [h.__dict__ for h in history if h]


@app.get("/api/realtime-sensors")
async def get_realtime_sensors_api(db: Session = Depends(get_db)):
    """获取实时传感器数据"""
    try:
        # 获取所有传感器的最新数据
        all_sensors = get_all_sensors_from_db(db)
        
        # 按设备分组
        sensors_by_device = {}
        for sensor in all_sensors:
            if sensor.device_id not in sensors_by_device:
                sensors_by_device[sensor.device_id] = []
            sensors_by_device[sensor.device_id].append(sensor)
        
        # 构造返回数据
        result = []
        for device_id, sensors in sensors_by_device.items():
            device_data = {
                'device_id': device_id,
                'sensors': []
            }
            
            for sensor in sensors:
                sensor_data = {
                    'id': sensor.id,
                    'type': sensor.type,
                    'value': sensor.value,
                    'unit': sensor.unit,
                    'timestamp': sensor.timestamp,
                    'alert_status': sensor.alert_status
                }
                device_data['sensors'].append(sensor_data)
            
            result.append(device_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/latest-sensors")
async def get_latest_sensors_api(db: Session = Depends(get_db)):
    """获取最新的传感器数据（仅返回最新记录，用于实时显示）"""
    try:
        # 获取所有设备的最新传感器数据
        latest_sensors = get_latest_sensors_from_db(db)
        
        # 按设备分组
        sensors_by_device = {}
        for sensor in latest_sensors:
            if sensor.device_id not in sensors_by_device:
                sensors_by_device[sensor.device_id] = []
            sensors_by_device[sensor.device_id].append(sensor)
        
        # 构造返回数据
        result = []
        for device_id, sensors in sensors_by_device.items():
            device_data = {
                'device_id': device_id,
                'sensors': []
            }
            
            for sensor in sensors:
                sensor_data = {
                    'id': sensor.id,
                    'type': sensor.type,
                    'value': sensor.value,
                    'unit': sensor.unit,
                    'timestamp': sensor.timestamp,
                    'alert_status': sensor.alert_status
                }
                device_data['sensors'].append(sensor_data)
            
            result.append(device_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# MQTT配置相关API
@app.get("/api/mqtt-configs", response_model=List[MQTTConfig])
async def get_mqtt_configs_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    configs = get_mqtt_configs(db, skip=skip, limit=limit)
    return configs


@app.get("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def get_mqtt_config_api(config_id: int, db: Session = Depends(get_db)):
    config = get_mqtt_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return config


@app.post("/api/mqtt-configs", response_model=MQTTConfig)
async def create_mqtt_config_api(config: MQTTConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = create_mqtt_config(db, config_data)
    return result


@app.put("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def update_mqtt_config_api(config_id: int, config: MQTTConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = update_mqtt_config(db, config_id, config_data)
    if not result:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return result


@app.delete("/api/mqtt-configs/{config_id}")
async def delete_mqtt_config_api(config_id: int, db: Session = Depends(get_db)):
    success = delete_mqtt_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return {"message": "MQTT Config deleted successfully"}


# 主题配置相关API
@app.get("/api/topic-configs", response_model=List[TopicConfig])
async def get_topic_configs_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    configs = get_topic_configs(db, skip=skip, limit=limit)
    return configs


@app.get("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def get_topic_config_api(config_id: int, db: Session = Depends(get_db)):
    config = get_topic_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return config


@app.post("/api/topic-configs", response_model=TopicConfig)
async def create_topic_config_api(config: TopicConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = create_topic_config(db, config_data)
    return result


@app.put("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def update_topic_config_api(config_id: int, config: TopicConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = update_topic_config(db, config_id, config_data)
    if not result:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return result


@app.delete("/api/topic-configs/{config_id}")
async def delete_topic_config_api(config_id: int, db: Session = Depends(get_db)):
    success = delete_topic_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return {"message": "Topic Config deleted successfully"}


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


def get_device_history_from_db(db: Session, device_id: int) -> List[SensorDataModel]:
    """获取设备的历史传感器数据"""
    # 获取设备的传感器数据，按时间倒序排列，限制为最近100条
    return db.query(SensorDataModel).filter(
        SensorDataModel.device_id == device_id
    ).order_by(SensorDataModel.timestamp.desc()).limit(100).all()


def get_all_sensors_from_db(db: Session) -> List[SensorDataModel]:
    """获取所有传感器数据"""
    return db.query(SensorDataModel).all()


def get_latest_sensors_from_db(db: Session) -> List[SensorDataModel]:
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
