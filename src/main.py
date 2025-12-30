from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import random
import socket
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import ConfigDict


# 添加CORS支持
from fastapi.middleware.cors import CORSMiddleware

# 为Windows系统设置兼容的事件循环策略
import sys
if sys.platform == "win32":
    # 使用SelectorEventLoop而不是ProactorEventLoop，更适合网络操作
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


app = FastAPI(title="安阳工学院IOT管理系统")

# 添加CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应指定具体域名，而不是使用"*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取当前文件的目录，然后构建静态目录的路径
current_dir = Path(__file__).parent
static_dir = current_dir / "static"

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# SQLite数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./iot_system.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DeviceModel(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    device_type = Column(String)
    status = Column(String)
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
    name = Column(String, unique=True, index=True)  # 配置名称
    server = Column(String, default='172.16.208.176')
    port = Column(Integer, default=18883)
    username = Column(String, default='qxy1')
    password = Column(String, default='5686670')
    client_id = Column(String, default='python_client')
    keepalive = Column(Integer, default=60)
    timeout = Column(Integer, default=10)
    use_tls = Column(Boolean, default=False)
    ca_certs = Column(String, nullable=True)
    certfile = Column(String, nullable=True)
    keyfile = Column(String, nullable=True)
    will_topic = Column(String, default='clients/python_client_status')
    will_payload = Column(String, default='Client is offline')
    will_qos = Column(Integer, default=1)
    is_active = Column(Boolean, default=False)  # 是否为当前激活配置
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopicConfigModel(Base):
    __tablename__ = "topic_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # 配置名称
    mqtt_config_id = Column(Integer, nullable=False)  # 关联的MQTT配置ID
    subscribe_topics = Column(Text)  # 订阅主题，JSON格式存储
    publish_topic = Column(String)  # 发布主题
    data_format = Column(String)  # 数据格式，如JSON, CSV等
    device_mapping = Column(Text)  # 设备映射规则，JSON格式存储
    is_active = Column(Boolean, default=False)  # 是否激活
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 创建数据库表
Base.metadata.create_all(bind=engine)


def migrate_database():
    """数据库迁移函数，处理新增字段"""
    import sqlite3
    from sqlalchemy import text
    
    # 连接数据库
    db_conn = sqlite3.connect("iot_system.db")
    cursor = db_conn.cursor()
    
    # 检查mqtt_config_id列是否存在
    cursor.execute("PRAGMA table_info(devices)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "mqtt_config_id" not in columns:
        # 由于SQLite不支持直接添加列，我们需要重新创建表
        # 1. 重命名原表
        cursor.execute("ALTER TABLE devices RENAME TO devices_backup")
        
        # 2. 创建新表（包含新列）
        cursor.execute("""
            CREATE TABLE devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                device_type VARCHAR,
                status VARCHAR,
                location VARCHAR,
                mqtt_config_id INTEGER,
                topic_config_id INTEGER
            )
        """)
        
        # 3. 将数据从备份表复制到新表
        cursor.execute("""
            INSERT INTO devices (id, name, device_type, status, location)
            SELECT id, name, device_type, status, location
            FROM devices_backup
        """)
        
        # 4. 删除备份表
        cursor.execute("DROP TABLE devices_backup")
        
        # 提交更改
        db_conn.commit()
        print("数据库迁移完成：已添加mqtt_config_id和topic_config_id字段")
    
    if "topic_config_id" not in columns:
        print("topic_config_id字段也已添加")
    
    # 关闭连接
    db_conn.close()


# 执行数据库迁移
migrate_database()


class SensorData(BaseModel):
    id: int
    type: str
    value: float
    unit: str
    timestamp: datetime
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    alert_status: str = "normal"  # normal, warning, alert

    model_config = ConfigDict(from_attributes=True)


class Device(BaseModel):
    id: int
    name: str  # 设备名称
    device_type: str  # 设备类型
    status: str
    location: str
    mqtt_config_id: Optional[int] = None  # 关联的MQTT配置ID
    topic_config_id: Optional[int] = None  # 关联的主题配置ID

    model_config = ConfigDict(from_attributes=True)


class MQTTConfig(BaseModel):
    id: int
    name: str
    server: str = '172.16.208.176'
    port: int = 18883
    username: str = 'qxy1'
    password: str = '5686670'
    client_id: str = 'python_client'
    keepalive: int = 60
    timeout: int = 10
    use_tls: bool = False
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    will_topic: str = 'clients/python_client_status'
    will_payload: str = 'Client is offline'
    will_qos: int = 1
    is_active: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MQTTConfigCreate(BaseModel):
    name: str
    server: str = '172.16.208.176'
    port: int = 18883
    username: str = 'qxy1'
    password: str = '5686670'
    client_id: str = 'python_client'
    keepalive: int = 60
    timeout: int = 10
    use_tls: bool = False
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    will_topic: str = 'clients/python_client_status'
    will_payload: str = 'Client is offline'
    will_qos: int = 1

    model_config = ConfigDict(from_attributes=True)


class MQTTConfigUpdate(BaseModel):
    name: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    keepalive: Optional[int] = None
    timeout: Optional[int] = None
    use_tls: Optional[bool] = None
    ca_certs: Optional[str] = None
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    will_topic: Optional[str] = None
    will_payload: Optional[str] = None
    will_qos: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TopicConfig(BaseModel):
    id: int
    name: str
    mqtt_config_id: int
    subscribe_topics: Optional[str] = None  # JSON格式的订阅主题列表
    publish_topic: Optional[str] = None
    data_format: Optional[str] = 'JSON'  # 默认数据格式
    device_mapping: Optional[str] = None  # JSON格式的设备映射规则
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TopicConfigCreate(BaseModel):
    name: str
    mqtt_config_id: int
    subscribe_topics: Optional[str] = None
    publish_topic: Optional[str] = None
    data_format: Optional[str] = 'JSON'
    device_mapping: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TopicConfigUpdate(BaseModel):
    name: Optional[str] = None
    mqtt_config_id: Optional[int] = None
    subscribe_topics: Optional[str] = None
    publish_topic: Optional[str] = None
    data_format: Optional[str] = None
    device_mapping: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    mqtt_config_id: Optional[int] = None
    topic_config_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    name: str
    device_type: str
    status: str = "离线"
    location: str = ""
    mqtt_config_id: Optional[int] = None
    topic_config_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceWithSensors(BaseModel):
    id: int
    name: str
    device_type: str
    status: str
    location: str
    last_seen: datetime
    sensors: List[SensorData]

    model_config = ConfigDict(from_attributes=True)


# 数据库操作函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_devices_from_db(db: Session):
    return db.query(DeviceModel).all()


def get_device_by_id(db: Session, device_id: int):
    return db.query(DeviceModel).filter(DeviceModel.id == device_id).first()


def create_device_in_db(db: Session, device: DeviceCreate) -> DeviceModel:
    """创建设备到数据库"""
    db_device = DeviceModel(
        name=device.name,
        device_type=device.device_type,
        status="离线",  # 新设备默认离线
        location=device.location,
        mqtt_config_id=device.mqtt_config_id,
        topic_config_id=device.topic_config_id
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device_in_db(db: Session, device_id: int, device: DeviceUpdate) -> Optional[DeviceModel]:
    """更新数据库中的设备"""
    db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
    if db_device:
        if device.name is not None:
            db_device.name = device.name
        if device.device_type is not None:
            db_device.device_type = device.device_type
        if device.location is not None:
            db_device.location = device.location
        if device.mqtt_config_id is not None:
            db_device.mqtt_config_id = device.mqtt_config_id
        if device.topic_config_id is not None:
            db_device.topic_config_id = device.topic_config_id
        
        db.commit()
        db.refresh(db_device)
        return db_device
    return None


def delete_device_from_db(db: Session, device_id: int) -> bool:
    """从数据库中删除设备"""
    db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
    if db_device:
        # 同时删除相关传感器
        db.query(SensorDataModel).filter(SensorDataModel.device_id == device_id).delete()
        db.delete(db_device)
        db.commit()
        return True
    return False


def get_sensors_from_db(db: Session) -> List[SensorDataModel]:
    """从数据库获取所有传感器数据"""
    return db.query(SensorDataModel).all()


def get_device_sensors_from_db(db: Session, device_id: int) -> List[SensorDataModel]:
    """根据设备ID从数据库获取传感器数据"""
    return db.query(SensorDataModel).filter(SensorDataModel.device_id == device_id).all()


def update_sensor_values_in_db(db: Session) -> None:
    """更新数据库中传感器的值"""
    sensors = db.query(SensorDataModel).all()
    for sensor in sensors:
        if sensor.value != 0:  # 离线设备的传感器值为0，不更新
            if sensor.type == '温度传感器':
                sensor.value = round(random.uniform(20, 30), 1)
            elif sensor.type == '湿度传感器':
                sensor.value = round(random.uniform(50, 70), 1)
            elif sensor.type == '光照传感器':
                sensor.value = round(random.uniform(100, 500), 1)
            elif sensor.type == '气压传感器':
                sensor.value = round(random.uniform(980, 1030), 1)
            elif sensor.type == 'PM2.5传感器':
                sensor.value = round(random.uniform(0, 50), 1)
            elif sensor.type == '噪音传感器':
                sensor.value = round(random.uniform(30, 60), 1)
        
        # 更新传感器状态
        if sensor.type == '温度传感器' and sensor.value > 28:
            sensor.alert_status = 'alert' if sensor.value > 30 else 'warning'
        elif sensor.type == '湿度传感器' and sensor.value > 65:
            sensor.alert_status = 'alert' if sensor.value > 70 else 'warning'
        else:
            sensor.alert_status = 'normal'
    
    db.commit()


# MQTT配置数据库操作函数
def get_mqtt_configs_from_db(db: Session):
    """获取所有MQTT配置"""
    return db.query(MQTTConfigModel).all()


def get_mqtt_config_by_id(db: Session, config_id: int):
    """根据ID获取MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()


def get_active_mqtt_config(db: Session):
    """获取当前激活的MQTT配置"""
    return db.query(MQTTConfigModel).filter(MQTTConfigModel.is_active == True).first()


def create_mqtt_config_in_db(db: Session, config: MQTTConfigCreate):
    """创建MQTT配置"""
    db_config = MQTTConfigModel(
        name=config.name,
        server=config.server,
        port=config.port,
        username=config.username,
        password=config.password,
        client_id=config.client_id,
        keepalive=config.keepalive,
        timeout=config.timeout,
        use_tls=config.use_tls,
        ca_certs=config.ca_certs,
        certfile=config.certfile,
        keyfile=config.keyfile,
        will_topic=config.will_topic,
        will_payload=config.will_payload,
        will_qos=config.will_qos
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_mqtt_config_in_db(db: Session, config_id: int, config: MQTTConfigUpdate):
    """更新MQTT配置"""
    db_config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if db_config:
        # 更新提供的字段
        for field, value in config.model_dump(exclude_unset=True).items():
            setattr(db_config, field, value)
        db.commit()
        db.refresh(db_config)
        return db_config
    return None


def delete_mqtt_config_from_db(db: Session, config_id: int):
    """删除MQTT配置"""
    db_config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if db_config:
        # 如果删除的是激活配置，需要特殊处理
        if db_config.is_active:
            # 设置另一个配置为激活状态，或者将激活状态设为False
            other_configs = db.query(MQTTConfigModel).filter(
                MQTTConfigModel.id != config_id
            ).limit(1).all()
            if other_configs:
                other_configs[0].is_active = True
        db.delete(db_config)
        db.commit()
        return True
    return False


def activate_mqtt_config_in_db(db: Session, config_id: int):
    """激活指定的MQTT配置，将其他配置设为非激活状态"""
    # 将所有配置设为非激活
    db.query(MQTTConfigModel).update({MQTTConfigModel.is_active: False})
    
    # 激活指定配置
    db_config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if db_config:
        db_config.is_active = True
        db.commit()
        return True
    return False


def get_topic_configs_from_db(db: Session):
    """获取所有主题配置"""
    return db.query(TopicConfigModel).all()


def get_topic_config_by_id(db: Session, config_id: int):
    """根据ID获取主题配置"""
    return db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()


def get_active_topic_config(db: Session):
    """获取激活的主题配置"""
    return db.query(TopicConfigModel).filter(TopicConfigModel.is_active == True).first()


def create_topic_config_in_db(db: Session, config: TopicConfigCreate):
    """创建主题配置"""
    db_config = TopicConfigModel(
        name=config.name,
        mqtt_config_id=config.mqtt_config_id,
        subscribe_topics=config.subscribe_topics,
        publish_topic=config.publish_topic,
        data_format=config.data_format,
        device_mapping=config.device_mapping,
        is_active=False  # 默认不激活
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_topic_config_in_db(db: Session, config_id: int, config: TopicConfigUpdate):
    """更新主题配置"""
    db_config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if db_config:
        for field, value in config.model_dump(exclude_unset=True).items():
            setattr(db_config, field, value)
        db.commit()
        db.refresh(db_config)
        return db_config
    return None


def delete_topic_config_from_db(db: Session, config_id: int):
    """删除主题配置"""
    db_config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if db_config:
        # 如果删除的是激活配置，激活其他配置
        if db_config.is_active:
            other_configs = db.query(TopicConfigModel).filter(
                TopicConfigModel.id != config_id
            ).all()
            if other_configs:
                # 激活第一个其他配置
                other_configs[0].is_active = True
        
        db.delete(db_config)
        db.commit()
        return True
    return False


def activate_topic_config_in_db(db: Session, config_id: int):
    """激活指定的主题配置，将其他配置设为非激活状态"""
    # 将所有配置设为非激活
    db.query(TopicConfigModel).update({TopicConfigModel.is_active: False})
    
    # 激活指定配置
    db_config = db.query(TopicConfigModel).filter(TopicConfigModel.id == config_id).first()
    if db_config:
        db_config.is_active = True
        db.commit()
        return True
    return False


# 初始化数据库数据
def init_db_data():
    db = SessionLocal()
    try:
        # 检查数据库是否完全为空（没有任何表的数据）
        device_count = db.query(DeviceModel).count()
        sensor_count = db.query(SensorDataModel).count()
        config_count = db.query(MQTTConfigModel).count()
        
        # 只有在所有表都为空时才初始化数据（即第一次运行）
        if device_count == 0 and sensor_count == 0 and config_count == 0:
            # 添加默认设备
            default_devices = [
                DeviceModel(name='实验室设备A', device_type='温湿度监测设备', status='在线', location='实验室1'),
                DeviceModel(name='实验室设备B', device_type='环境监测设备', status='在线', location='实验室2'),
                DeviceModel(name='环境监测站C', device_type='多参数监测设备', status='离线', location='实验室3')
            ]
            for device in default_devices:
                db.add(device)
            db.commit()
        
            # 为设备添加默认传感器
            for device in default_devices:
                # 重新获取设备以获取其ID
                db_device = db.query(DeviceModel).filter(DeviceModel.name == device.name).first()
                sensors_data = []
                
                if device.name == '实验室设备A':
                    sensors_data = [
                        SensorDataModel(device_id=db_device.id, type='温度传感器', value=round(random.uniform(20, 30), 1), 
                                       unit='°C', timestamp=datetime.now(), min_value=15, max_value=35, alert_status='normal'),
                        SensorDataModel(device_id=db_device.id, type='湿度传感器', value=round(random.uniform(50, 70), 1), 
                                       unit='%', timestamp=datetime.now(), min_value=40, max_value=80, alert_status='normal'),
                        SensorDataModel(device_id=db_device.id, type='光照传感器', value=round(random.uniform(100, 500), 1), 
                                       unit='lux', timestamp=datetime.now(), min_value=50, max_value=1000, alert_status='normal')
                    ]
                elif device.name == '实验室设备B':
                    sensors_data = [
                        SensorDataModel(device_id=db_device.id, type='温度传感器', value=round(random.uniform(20, 30), 1), 
                                       unit='°C', timestamp=datetime.now(), min_value=15, max_value=35, alert_status='normal'),
                        SensorDataModel(device_id=db_device.id, type='湿度传感器', value=round(random.uniform(50, 70), 1), 
                                       unit='%', timestamp=datetime.now(), min_value=40, max_value=80, alert_status='normal'),
                        SensorDataModel(device_id=db_device.id, type='气压传感器', value=round(random.uniform(980, 1030), 1), 
                                       unit='hPa', timestamp=datetime.now(), min_value=950, max_value=1050, alert_status='normal')
                    ]
                elif device.name == '环境监测站C':
                    sensors_data = [
                        SensorDataModel(device_id=db_device.id, type='温度传感器', value=0, 
                                       unit='°C', timestamp=datetime.now(), min_value=15, max_value=35, alert_status='normal'),
                        SensorDataModel(device_id=db_device.id, type='湿度传感器', value=0, 
                                       unit='%', timestamp=datetime.now(), min_value=40, max_value=80, alert_status='normal'),
                        SensorDataModel(device_id=db_device.id, type='PM2.5传感器', value=0, 
                                       unit='μg/m³', timestamp=datetime.now(), min_value=0, max_value=500, alert_status='normal'),
                        SensorDataModel(device_id=db_device.id, type='噪音传感器', value=0, 
                                       unit='dB', timestamp=datetime.now(), min_value=0, max_value=120, alert_status='normal')
                    ]
                
                for sensor in sensors_data:
                    db.add(sensor)
            
            db.commit()
        
        # 检查是否有MQTT配置数据
        if db.query(MQTTConfigModel).count() == 0:
            # 添加默认MQTT配置
            default_mqtt_config = MQTTConfigModel(
                name='默认MQTT配置',
                server='172.16.208.176',
                port=18883,
                username='qxy1',
                password='5686670',
                client_id='python_client',
                keepalive=60,
                timeout=10,
                use_tls=False,
                will_topic='clients/python_client_status',
                will_payload='Client is offline',
                will_qos=1,
                is_active=True  # 默认配置为激活状态
            )
            db.add(default_mqtt_config)
            db.commit()
    finally:
        db.close()


# 初始化数据
init_db_data()


# MQTT配置相关API

@app.get("/api/mqtt-configs", response_model=List[MQTTConfig])
async def get_mqtt_configs():
    db = SessionLocal()
    try:
        db_configs = get_mqtt_configs_from_db(db)
        configs = [MQTTConfig.model_validate(db_config) for db_config in db_configs]
        return configs
    finally:
        db.close()


@app.get("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def get_mqtt_config(config_id: int):
    db = SessionLocal()
    try:
        db_config = get_mqtt_config_by_id(db, config_id)
        if db_config:
            return MQTTConfig.model_validate(db_config)
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


@app.post("/api/mqtt-configs", response_model=MQTTConfig)
async def create_mqtt_config(config: MQTTConfigCreate):
    db = SessionLocal()
    try:
        db_config = create_mqtt_config_in_db(db, config)
        return MQTTConfig.model_validate(db_config)
    finally:
        db.close()


@app.put("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def update_mqtt_config(config_id: int, config: MQTTConfigUpdate):
    db = SessionLocal()
    try:
        db_config = update_mqtt_config_in_db(db, config_id, config)
        if db_config:
            return MQTTConfig.model_validate(db_config)
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


@app.delete("/api/mqtt-configs/{config_id}")
async def delete_mqtt_config(config_id: int):
    db = SessionLocal()
    try:
        success = delete_mqtt_config_from_db(db, config_id)
        if success:
            return JSONResponse(status_code=200, content={"message": "配置删除成功"})
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


@app.post("/api/mqtt-configs/{config_id}/activate")
async def activate_mqtt_config(config_id: int):
    db = SessionLocal()
    try:
        db_config = activate_mqtt_config_in_db(db, config_id)
        if db_config:
            return MQTTConfig.model_validate(db_config)
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


# 测试MQTT连接
@app.post("/api/mqtt-configs/{config_id}/test")
async def test_mqtt_config(config_id: int):
    # 这里实现测试连接的逻辑
    # 为了简化，我们返回一个模拟的响应
    try:
        # 在实际实现中，这里应该尝试连接到MQTT服务器
        # 这里我们模拟成功
        return JSONResponse(status_code=200, content={"message": f"配置ID {config_id} 连接测试成功"})
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"连接测试失败: {str(e)}"})


# 主题配置相关API
@app.get("/api/topic-configs", response_model=List[TopicConfig])
async def get_topic_configs():
    db = SessionLocal()
    try:
        db_configs = get_topic_configs_from_db(db)
        configs = [TopicConfig.model_validate(db_config) for db_config in db_configs]
        return configs
    finally:
        db.close()


@app.get("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def get_topic_config(config_id: int):
    db = SessionLocal()
    try:
        db_config = get_topic_config_by_id(db, config_id)
        if db_config:
            return TopicConfig.model_validate(db_config)
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


@app.post("/api/topic-configs", response_model=TopicConfig)
async def create_topic_config(config: TopicConfigCreate):
    db = SessionLocal()
    try:
        db_config = create_topic_config_in_db(db, config)
        return TopicConfig.model_validate(db_config)
    finally:
        db.close()


@app.put("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def update_topic_config(config_id: int, config: TopicConfigUpdate):
    db = SessionLocal()
    try:
        db_config = update_topic_config_in_db(db, config_id, config)
        if db_config:
            return TopicConfig.model_validate(db_config)
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


@app.delete("/api/topic-configs/{config_id}")
async def delete_topic_config(config_id: int):
    db = SessionLocal()
    try:
        success = delete_topic_config_from_db(db, config_id)
        if success:
            return JSONResponse(status_code=200, content={"message": "主题配置删除成功"})
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


@app.post("/api/topic-configs/{config_id}/activate")
async def activate_topic_config(config_id: int):
    db = SessionLocal()
    try:
        success = activate_topic_config_in_db(db, config_id)
        if success:
            return JSONResponse(status_code=200, content={"message": "主题配置激活成功"})
        else:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
    finally:
        db.close()


@app.get("/api/topic-configs/active", response_model=Optional[TopicConfig])
async def get_active_topic_config():
    db = SessionLocal()
    try:
        db_config = get_active_topic_config(db)
        if db_config:
            return TopicConfig.model_validate(db_config)
        else:
            return None
    finally:
        db.close()


@app.get("/")
async def read_root():
    # 返回一个简单的页面，提示用户访问前端
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>安阳工学院IOT管理系统</title>
    </head>
    <body>
        <div style="text-align: center; margin-top: 50px;">
            <h1>安阳工学院IOT管理系统</h1>
            <p>后端API服务运行正常</p>
            <p>请访问前端应用（通常在端口3000）以使用完整功能</p>
            <p>API文档请访问: <a href="/docs">/docs</a></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/devices", response_model=List[Device])
async def get_devices():
    """获取所有设备"""
    db = SessionLocal()
    try:
        db_devices = get_devices_from_db(db)
        devices = [Device.model_validate(db_device) for db_device in db_devices]
        return devices
    finally:
        db.close()


@app.get("/api/devices/{device_id}", response_model=Device)
async def get_device(device_id: int):
    """获取单个设备"""
    db = SessionLocal()
    try:
        db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
        if db_device is None:
            raise HTTPException(status_code=404, detail="设备未找到")
        return Device.model_validate(db_device)
    finally:
        db.close()


@app.post("/api/devices", response_model=Device)
async def add_device(device: DeviceCreate):
    """添加新设备"""
    db = SessionLocal()
    try:
        db_device = create_device_in_db(db, device)
        return Device.model_validate(db_device)
    finally:
        db.close()


@app.put("/api/devices/{device_id}", response_model=Device)
async def update_device(device_id: int, device: DeviceUpdate):
    """更新设备信息"""
    db = SessionLocal()
    try:
        db_device = update_device_in_db(db, device_id, device)
        if db_device:
            return Device.model_validate(db_device)
        else:
            return JSONResponse(status_code=404, content={"message": "设备未找到"})
    finally:
        db.close()


@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: int):
    db = SessionLocal()
    try:
        success = delete_device_from_db(db, device_id)
        if success:
            return JSONResponse(status_code=200, content={"message": "设备删除成功"})
        else:
            return JSONResponse(status_code=404, content={"message": "设备未找到"})
    finally:
        db.close()


@app.get("/api/sensors", response_model=List[SensorData])
async def get_sensors():
    """获取所有传感器数据"""
    db = SessionLocal()
    try:
        db_sensors = get_sensors_from_db(db)
        sensors = [SensorData.model_validate(db_sensor) for db_sensor in db_sensors]
        return sensors
    finally:
        db.close()


@app.get("/api/devices/{device_id}/sensors", response_model=List[SensorData])
async def get_device_sensors(device_id: int):
    """获取指定设备的传感器数据"""
    db = SessionLocal()
    try:
        db_sensors = get_device_sensors_from_db(db, device_id)
        sensors = [SensorData.model_validate(db_sensor) for db_sensor in db_sensors]
        return sensors
    finally:
        db.close()


# 添加历史数据API
@app.get("/api/devices/{device_id}/history", response_model=List[Dict])
async def get_device_history(device_id: int, sensor_type: str, hours: int = 24):
    # 模拟生成历史数据
    history = []
    now = datetime.now()
    for i in range(hours * 4):  # 每15分钟一个数据点
        timestamp = now - timedelta(minutes=i*15)
        value = round(random.uniform(20, 30), 1)
        history.append({
            "timestamp": timestamp.isoformat(),
            "value": value
        })
    return history


# 更新设备数据的模拟函数
async def update_device_data():
    while True:
        await asyncio.sleep(3)  # 每3秒更新一次
        db = SessionLocal()
        try:
            update_sensor_values_in_db(db)
        finally:
            db.close()


# 启动时运行更新设备数据的任务
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_device_data())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)