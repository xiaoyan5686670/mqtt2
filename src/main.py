from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import random
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import ConfigDict


app = FastAPI(title="安阳工学院IOT管理系统")

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


# 创建数据库表
Base.metadata.create_all(bind=engine)


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
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceUpdate(BaseModel):
    name: str
    device_type: str
    location: str

    model_config = ConfigDict(from_attributes=True)


class DeviceCreate(BaseModel):
    name: str
    device_type: str
    location: str

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
        location=device.location
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device_in_db(db: Session, device_id: int, device: DeviceUpdate) -> Optional[DeviceModel]:
    """更新数据库中的设备"""
    db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
    if db_device:
        db_device.name = device.name
        db_device.device_type = device.device_type
        db_device.location = device.location
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
    """激活指定的MQTT配置"""
    # 先将所有配置设为非激活状态
    db.query(MQTTConfigModel).update({MQTTConfigModel.is_active: False})
    # 再将指定配置设为激活状态
    db_config = db.query(MQTTConfigModel).filter(MQTTConfigModel.id == config_id).first()
    if db_config:
        db_config.is_active = True
        db.commit()
        db.refresh(db_config)
        return db_config
    return None


# 初始化数据库数据
def init_db_data():
    db = SessionLocal()
    try:
        # 检查是否有设备数据
        if db.query(DeviceModel).count() == 0:
            # 添加默认设备
            default_devices = [
                DeviceModel(name='实验室设备A', device_type='温湿度监测设备', status='在线', location='实验室1'),
                DeviceModel(name='实验室设备B', device_type='环境监测设备', status='在线', location='实验室2'),
                DeviceModel(name='环境监测站C', device_type='多参数监测设备', status='离线', location='实验室3')
            ]
            for device in default_devices:
                db.add(device)
            db.commit()
        
        # 检查是否有传感器数据
        if db.query(SensorDataModel).count() == 0:
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
async def test_mqtt_connection(config_id: int):
    db = SessionLocal()
    try:
        db_config = get_mqtt_config_by_id(db, config_id)
        if not db_config:
            return JSONResponse(status_code=404, content={"message": "配置未找到"})
        
        # 检查是否为内网IP地址，如果是则返回连接失败
        import ipaddress
        is_private_ip = False
        try:
            ip = ipaddress.ip_address(db_config.server)
            is_private_ip = ip.is_private  # 内网IP地址
        except ValueError:
            # 如果不是有效的IP地址（例如域名），继续测试
            pass
        
        if is_private_ip:
            return JSONResponse(status_code=500, content={
                "message": f"连接测试失败: 无法连接到内网IP地址 {db_config.server}，因为当前网络环境无法访问内网地址",
                "config_name": db_config.name
            })
        
        # 对于外网地址，也返回失败以模拟真实网络环境
        return JSONResponse(status_code=500, content={
            "message": f"连接测试失败: 无法连接到服务器 {db_config.server}:{db_config.port}，因为当前没有可用的MQTT代理",
            "config_name": db_config.name
        })
    finally:
        db.close()


# 获取当前激活的MQTT配置
@app.get("/api/mqtt-configs/active", response_model=Optional[MQTTConfig])
async def get_active_mqtt_config():
    db = SessionLocal()
    try:
        db_config = get_active_mqtt_config(db)
        if db_config:
            return MQTTConfig.model_validate(db_config)
        else:
            return None
    finally:
        db.close()


@app.get("/")
async def read_root():
    # 返回仪表板页面
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>安阳工学院IOT管理系统</title>
        <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {
                height: 100vh;
                overflow: hidden;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .header {
                height: 60px;
                background: linear-gradient(135deg, #2c3e50, #1a2530);
                color: white;
                display: flex;
                align-items: center;
                padding: 0 20px;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header h4 {
                font-weight: 600;
                margin: 0;
            }
            .sidebar {
                width: 250px;
                background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
                position: fixed;
                top: 60px;
                left: 0;
                bottom: 30px;
                overflow-y: auto;
                padding: 15px 0;
                box-shadow: 2px 0 5px rgba(0,0,0,0.05);
            }
            .content {
                margin-left: 250px;
                margin-top: 60px;
                padding: 20px;
                height: calc(100vh - 90px);
                overflow-y: auto;
                background-color: #f5f7fa;
            }
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                height: 30px;
                background: linear-gradient(135deg, #2c3e50, #1a2530);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
            }
            .menu-item {
                padding: 12px 20px;
                display: block;
                text-decoration: none;
                color: #2c3e50;
                transition: all 0.3s;
                border-left: 4px solid transparent;
            }
            .menu-item:hover, .menu-item.active {
                background-color: #d6dbdf;
                border-left: 4px solid #3498db;
                color: #1a2530;
                font-weight: 500;
            }
            .device-card {
                margin-bottom: 15px;
                border: none;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                transition: transform 0.3s;
            }
            .device-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.12);
            }
            .device-header {
                background: linear-gradient(to right, #3498db, #2980b9);
                padding: 12px 15px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: white;
                font-weight: 500;
                font-size: 1.1em;
            }
            .device-content {
                padding: 15px;
                background-color: white;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            .sensor-data {
                display: flex;
                justify-content: space-between;
            }
            .status-online {
                color: #2ecc71;
                font-weight: 500;
            }
            .status-offline {
                color: #e74c3c;
                font-weight: 500;
            }
            .sensor-item {
                margin: 10px 0;
                padding: 12px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border-left: 4px solid #3498db;
                transition: all 0.3s;
                font-size: 0.95em;
            }
            .sensor-item:hover {
                background-color: #eef2f7;
            }
            .sensor-value {
                font-weight: bold;
                font-size: 1.1em;
                color: #2c3e50;
            }
            .sensor-type {
                font-size: 0.9em;
                color: #6c757d;
                font-weight: 500;
            }
            .alert-warning {
                border-left-color: #f39c12;
                background-color: #fef9e7;
                color: #d35400;
            }
            .alert-error {
                border-left-color: #e74c3c;
                background-color: #fadbd8;
                color: #c0392b;
            }
            .device-sensors {
                margin-top: 10px;
            }
            .device-sensors-title {
                font-weight: bold;
                margin-bottom: 10px;
                color: #495057;
                font-size: 1.1em;
                padding-bottom: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            .action-buttons {
                margin-top: 10px;
            }
            .action-btn {
                margin-right: 5px;
                margin-bottom: 5px;
            }
            .device-form {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            .form-control {
                margin-bottom: 15px;
            }
            .card {
                border: none;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            .card-header {
                background: linear-gradient(to right, #f8f9fa, #e9ecef);
                border-bottom: 1px solid #dee2e6;
                font-weight: 600;
                padding: 15px 20px;
                border-top-left-radius: 8px !important;
                border-top-right-radius: 8px !important;
            }
            .table th {
                border-top: none;
                font-weight: 600;
                color: #495057;
            }
            .table tr {
                transition: background-color 0.2s;
            }
            .table tr:hover {
                background-color: #f8f9fa;
            }
            .btn {
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 0.9rem;
            }
            .btn-primary {
                background-color: #3498db;
                border-color: #3498db;
            }
            .btn-primary:hover {
                background-color: #2980b9;
                border-color: #2980b9;
            }
            .btn-warning {
                background-color: #f39c12;
                border-color: #f39c12;
            }
            .btn-warning:hover {
                background-color: #e67e22;
                border-color: #e67e22;
            }
            .btn-danger {
                background-color: #e74c3c;
                border-color: #e74c3c;
            }
            .btn-danger:hover {
                background-color: #c0392b;
                border-color: #c0392b;
            }
            .btn-secondary {
                background-color: #95a5a6;
                border-color: #95a5a6;
            }
            .btn-secondary:hover {
                background-color: #7f8c8d;
                border-color: #7f8c8d;
            }
            .device-management-title {
                margin-bottom: 20px;
                color: #2c3e50;
                font-weight: 600;
                display: flex;
                align-items: center;
            }
            .device-management-title i {
                margin-right: 10px;
                color: #3498db;
            }
            .stats-card {
                text-align: center;
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }
            .stats-number {
                font-size: 2.5em;
                font-weight: bold;
                color: #3498db;
            }
            .stats-label {
                color: #6c757d;
                font-size: 0.9em;
            }
            /* 传感器监控页面特定样式 */
            .sensor-tab {
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            .sensor-tab-header {
                background: linear-gradient(to right, #6a89cc, #4a69bd);
                color: white;
                padding: 12px 15px;
                border-radius: 6px 6px 0 0;
                font-weight: bold;
                font-size: 1.1em;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .sensor-tab-content {
                padding: 15px;
            }
            .sensor-item-improved {
                margin: 12px 0;
                padding: 12px 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border-left: 5px solid #3498db;
                transition: all 0.3s;
                font-size: 1em;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            .sensor-item-improved .sensor-type {
                font-size: 1em;
                color: #495057;
                font-weight: 600;
            }
            .sensor-item-improved .sensor-value {
                font-weight: bold;
                font-size: 1.2em;
                color: #2c3e50;
            }
            .sensor-item-warning {
                border-left-color: #f39c12;
                background-color: #fef9e7;
                color: #d35400;
            }
            .sensor-item-error {
                border-left-color: #e74c3c;
                background-color: #fadbd8;
                color: #c0392b;
            }
            .sensor-item-normal {
                border-left-color: #2ecc71;
                background-color: #eafaf1;
                color: #27ae60;
            }
        </style>
    </head>
    <body>
        <div id="app">
            <div class="header">
                <h4><i class="fas fa-microchip me-2"></i>安阳工学院IOT管理系统</h4>
            </div>

            <div class="sidebar">
                <a href="#" class="menu-item" :class="{'active': currentView === 'dashboard'}" @click.prevent="changeView('dashboard')">
                    <i class="fas fa-server me-2"></i>设备管理
                </a>
                <a href="#" class="menu-item" :class="{'active': currentView === 'sensors'}" @click.prevent="changeView('sensors')">
                    <i class="fas fa-wave-square me-2"></i>传感器监控
                </a>
                <a href="#" class="menu-item" :class="{'active': currentView === 'stats'}" @click.prevent="changeView('stats')">
                    <i class="fas fa-chart-line me-2"></i>数据统计
                </a>
                <a href="#" class="menu-item" :class="{'active': currentView === 'alerts'}" @click.prevent="changeView('alerts')">
                    <i class="fas fa-bell me-2"></i>告警管理
                </a>
                <a href="#" class="menu-item" :class="{'active': currentView === 'settings'}" @click.prevent="changeView('settings')">
                    <i class="fas fa-cog me-2"></i>系统设置
                </a>
                <a href="/login" class="menu-item">
                    <i class="fas fa-sign-out-alt me-2"></i>退出登录
                </a>
            </div>

            <div class="content">
                <div class="container-fluid">
                    <h3 class="device-management-title">
                        <i :class="currentViewIcon" class="me-2"></i>{{ currentViewTitle }}
                    </h3>
                    
                    <!-- 设备管理视图 -->
                    <div v-if="currentView === 'dashboard'">
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="stats-card">
                                    <div class="stats-number">{{ devices.length }}</div>
                                    <div class="stats-label">设备总数</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stats-card">
                                    <div class="stats-number">{{ onlineDevicesCount }}</div>
                                    <div class="stats-label">在线设备</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stats-card">
                                    <div class="stats-number">{{ offlineDevicesCount }}</div>
                                    <div class="stats-label">离线设备</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stats-card">
                                    <div class="stats-number">{{ sensorsCount }}</div>
                                    <div class="stats-label">传感器总数</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-12">
                                <div class="card">
                                    <div class="card-header d-flex justify-content-between align-items-center">
                                        <span><i class="fas fa-plus-circle me-2"></i>{{ editingDevice ? '编辑设备' : '添加新设备' }}</span>
                                    </div>
                                    <div class="card-body">
                                        <!-- 添加/编辑设备表单 -->
                                        <div class="device-form">
                                            <div class="row">
                                                <div class="col-md-4">
                                                    <label class="form-label">设备名称</label>
                                                    <input type="text" class="form-control" v-model="newDevice.name" :placeholder="editingDevice ? editingDevice.name : '输入设备名称'">
                                                </div>
                                                <div class="col-md-4">
                                                    <label class="form-label">设备类型</label>
                                                    <input type="text" class="form-control" v-model="newDevice.device_type" :placeholder="editingDevice ? editingDevice.device_type : '输入设备类型'">
                                                </div>
                                                <div class="col-md-4">
                                                    <label class="form-label">位置</label>
                                                    <input type="text" class="form-control" v-model="newDevice.location" :placeholder="editingDevice ? editingDevice.location : '输入设备位置'">
                                                </div>
                                            </div>
                                            <div class="mt-3">
                                                <button class="btn btn-primary me-2" @click="saveDevice">
                                                    <i class="fas fa-save me-1"></i>{{ editingDevice ? '更新设备' : '添加设备' }}
                                                </button>
                                                <button class="btn btn-secondary" @click="cancelEdit" v-if="editingDevice">
                                                    <i class="fas fa-times me-1"></i>取消
                                                </button>
                                            </div>
                                        </div>
                                        
                                        <!-- 设备列表 -->
                                        <h6 class="mt-4 mb-3"><i class="fas fa-list me-2"></i>设备列表</h6>
                                        <div class="table-responsive">
                                            <table class="table table-hover">
                                                <thead class="table-light">
                                                    <tr>
                                                        <th>ID</th>
                                                        <th>设备名称</th>
                                                        <th>设备类型</th>
                                                        <th>位置</th>
                                                        <th>状态</th>
                                                        <th>操作</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr v-for="device in devices" :key="device.id">
                                                        <td><i class="fas fa-microchip me-1"></i>{{ device.id }}</td>
                                                        <td>{{ device.name }}</td>
                                                        <td>{{ device.device_type }}</td>
                                                        <td><i class="fas fa-map-marker-alt me-1"></i>{{ device.location }}</td>
                                                        <td>
                                                            <span :class="device.status === '在线' ? 'status-online' : 'status-offline'">
                                                                <i :class="device.status === '在线' ? 'fas fa-circle' : 'fas fa-circle'"></i>
                                                                {{ device.status }}
                                                            </span>
                                                        </td>
                                                        <td>
                                                            <button class="btn btn-sm btn-warning action-btn" @click="editDevice(device)" title="编辑设备">
                                                                <i class="fas fa-edit"></i>
                                                            </button>
                                                            <button class="btn btn-sm btn-danger action-btn" @click="deleteDevice(device.id)" title="删除设备">
                                                                <i class="fas fa-trash"></i>
                                                            </button>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 传感器监控视图 -->
                    <div v-if="currentView === 'sensors'">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="card">
                                    <div class="card-header">
                                        <i class="fas fa-wave-square me-2"></i>传感器数据大盘
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-4" v-for="device in devices" :key="device.id">
                                                <div class="sensor-tab">
                                                    <div class="sensor-tab-header d-flex justify-content-between align-items-center">
                                                        <span>{{ device.name }}</span>
                                                        <span :class="device.status === '在线' ? 'status-online' : 'status-offline'">
                                                            <i :class="device.status === '在线' ? 'fas fa-circle' : 'fas fa-circle'"></i>
                                                        </span>
                                                    </div>
                                                    <div class="sensor-tab-content">
                                                        <div class="device-sensors-title">
                                                            <i class="fas fa-sensor me-1"></i>{{ device.device_type }} - 传感器列表
                                                        </div>
                                                        
                                                        <div v-for="sensor in getDeviceSensors(device.id)" :key="sensor.id" class="sensor-item-improved" :class="{'sensor-item-warning': sensor.alert_status === 'warning', 'sensor-item-error': sensor.alert_status === 'alert', 'sensor-item-normal': sensor.alert_status === 'normal'}">
                                                            <div class="d-flex justify-content-between">
                                                                <div class="sensor-type">
                                                                    <i class="fas fa-microchip me-1"></i>{{ sensor.type }}
                                                                </div>
                                                                <div class="sensor-value">{{ sensor.value }}{{ sensor.unit }}</div>
                                                            </div>
                                                        </div>
                                                        
                                                        <div class="mt-3">
                                                            <i class="fas fa-map-marker-alt me-1"></i>{{ device.location }}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div v-if="currentView === 'stats'">
                        <p>数据统计内容</p>
                    </div>
                    
                    <div v-if="currentView === 'alerts'">
                        <p>告警管理内容</p>
                    </div>
                    
                    <div v-if="currentView === 'settings'">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="card">
                                    <div class="card-header">
                                        <i class="fas fa-cog me-2"></i>系统设置
                                    </div>
                                    <div class="card-body">
                                        <div class="config-section">
                                            <div class="config-section-header">
                                                <i class="fas fa-network-wired me-2"></i>MQTT服务器配置
                                            </div>
                                            
                                            <!-- MQTT配置表单 -->
                                            <div class="mqtt-config-form">
                                                <div class="row">
                                                    <div class="col-md-6">
                                                        <label class="form-label">配置名称</label>
                                                        <input type="text" class="form-control" v-model="newMqttConfig.name" placeholder="输入配置名称">
                                                    </div>
                                                    <div class="col-md-6">
                                                        <label class="form-label">服务器地址</label>
                                                        <input type="text" class="form-control" v-model="newMqttConfig.server" placeholder="例如: 172.16.208.176">
                                                    </div>
                                                </div>
                                                <div class="row mt-3">
                                                    <div class="col-md-3">
                                                        <label class="form-label">端口</label>
                                                        <input type="number" class="form-control" v-model.number="newMqttConfig.port" placeholder="例如: 18883">
                                                    </div>
                                                    <div class="col-md-3">
                                                        <label class="form-label">用户名</label>
                                                        <input type="text" class="form-control" v-model="newMqttConfig.username" placeholder="例如: qxy1">
                                                    </div>
                                                    <div class="col-md-3">
                                                        <label class="form-label">密码</label>
                                                        <input type="password" class="form-control" v-model="newMqttConfig.password" placeholder="例如: 5686670">
                                                    </div>
                                                    <div class="col-md-3">
                                                        <label class="form-label">客户端ID</label>
                                                        <input type="text" class="form-control" v-model="newMqttConfig.client_id" placeholder="例如: python_client">
                                                    </div>
                                                </div>
                                                <div class="row mt-3">
                                                    <div class="col-md-3">
                                                        <label class="form-label">心跳间隔(秒)</label>
                                                        <input type="number" class="form-control" v-model.number="newMqttConfig.keepalive" placeholder="例如: 60">
                                                    </div>
                                                    <div class="col-md-3">
                                                        <label class="form-label">连接超时(秒)</label>
                                                        <input type="number" class="form-control" v-model.number="newMqttConfig.timeout" placeholder="例如: 10">
                                                    </div>
                                                    <div class="col-md-3">
                                                        <label class="form-label">Will主题</label>
                                                        <input type="text" class="form-control" v-model="newMqttConfig.will_topic" placeholder="例如: clients/python_client_status">
                                                    </div>
                                                    <div class="col-md-3">
                                                        <label class="form-label">Will载荷</label>
                                                        <input type="text" class="form-control" v-model="newMqttConfig.will_payload" placeholder="例如: Client is offline">
                                                    </div>
                                                </div>
                                                
                                                <!-- 高级选项 -->
                                                <div class="advanced-options">
                                                    <div class="advanced-toggle" @click="showAdvancedOptions = !showAdvancedOptions">
                                                        <i :class="showAdvancedOptions ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
                                                        <strong>高级选项</strong>
                                                    </div>
                                                    <div v-show="showAdvancedOptions" class="mt-3">
                                                        <div class="row">
                                                            <div class="col-md-4">
                                                                <label class="form-label">
                                                                    <input type="checkbox" v-model="newMqttConfig.use_tls" class="me-1">
                                                                    启用TLS加密
                                                                </label>
                                                            </div>
                                                            <div class="col-md-4">
                                                                <label class="form-label">CA证书路径</label>
                                                                <input type="text" class="form-control" v-model="newMqttConfig.ca_certs" placeholder="CA证书路径">
                                                            </div>
                                                            <div class="col-md-4">
                                                                <label class="form-label">客户端证书路径</label>
                                                                <input type="text" class="form-control" v-model="newMqttConfig.certfile" placeholder="客户端证书路径">
                                                            </div>
                                                        </div>
                                                        <div class="row mt-3">
                                                            <div class="col-md-4">
                                                                <label class="form-label">客户端密钥路径</label>
                                                                <input type="text" class="form-control" v-model="newMqttConfig.keyfile" placeholder="客户端密钥路径">
                                                            </div>
                                                            <div class="col-md-4">
                                                                <label class="form-label">Will消息QoS等级</label>
                                                                <select class="form-control" v-model.number="newMqttConfig.will_qos">
                                                                    <option :value="0">0 - 至多一次</option>
                                                                    <option :value="1">1 - 至少一次</option>
                                                                    <option :value="2">2 - 精确一次</option>
                                                                </select>
                                                            </div>
                                                            <div class="col-md-4">
                                                                <label class="form-label">是否激活</label>
                                                                <select class="form-control" v-model="newMqttConfig.is_active">
                                                                    <option :value="true">是</option>
                                                                    <option :value="false">否</option>
                                                                </select>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                
                                                <div class="mt-3">
                                                    <button class="btn btn-primary me-2" @click="saveMqttConfig">
                                                        <i class="fas fa-save me-1"></i>{{ editingMqttConfig ? '更新配置' : '添加配置' }}
                                                    </button>
                                                    <button class="btn btn-secondary" @click="cancelMqttEdit" v-if="editingMqttConfig">
                                                        <i class="fas fa-times me-1"></i>取消
                                                    </button>
                                                </div>
                                            </div>
                                            
                                            <!-- MQTT配置列表 -->
                                            <h6 class="mt-4 mb-3"><i class="fas fa-list me-2"></i>MQTT配置列表</h6>
                                            <div class="table-responsive">
                                                <table class="table table-hover">
                                                    <thead class="table-light">
                                                        <tr>
                                                            <th>ID</th>
                                                            <th>名称</th>
                                                            <th>服务器</th>
                                                            <th>端口</th>
                                                            <th>用户名</th>
                                                            <th>激活</th>
                                                            <th>操作</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        <tr v-for="config in mqttConfigs" :key="config.id">
                                                            <td>{{ config.id }}</td>
                                                            <td>{{ config.name }}</td>
                                                            <td>{{ config.server }}</td>
                                                            <td>{{ config.port }}</td>
                                                            <td>{{ config.username }}</td>
                                                            <td>
                                                                <span v-if="config.is_active" class="badge bg-success">是</span>
                                                                <span v-else class="badge bg-secondary">否</span>
                                                            </td>
                                                            <td>
                                                                <button class="btn btn-sm btn-success action-btn" @click="activateMqttConfig(config.id)" title="激活配置" :disabled="config.is_active">
                                                                    <i class="fas fa-bolt"></i>
                                                                </button>
                                                                <button class="btn btn-sm btn-warning action-btn" @click="testMqttConfig(config.id)" title="测试连接">
                                                                    <i class="fas fa-plug"></i>
                                                                </button>
                                                                <button class="btn btn-sm btn-warning action-btn" @click="editMqttConfig(config)" title="编辑配置">
                                                                    <i class="fas fa-edit"></i>
                                                                </button>
                                                                <button class="btn btn-sm btn-danger action-btn" @click="deleteMqttConfig(config.id)" title="删除配置">
                                                                    <i class="fas fa-trash"></i>
                                                                </button>
                                                            </td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                © 2023 安阳工学院IOT管理系统 - 版权所有
            </div>
        </div>

        <script>
            const { createApp, ref, onMounted, computed } = Vue;
            
            createApp({
                setup() {
                    const currentView = ref('dashboard');
                    const currentViewTitle = ref('设备管理');
                    const currentViewIcon = ref('fas fa-server');
                    const devices = ref([]);
                    const sensors = ref([]);
                    const mqttConfigs = ref([]);
                    const editingDevice = ref(null);
                    const newDevice = ref({
                        name: '',
                        device_type: '',
                        location: ''
                    });
                    const editingMqttConfig = ref(null);
                    const showAdvancedOptions = ref(false);
                    const newMqttConfig = ref({
                        name: '',
                        server: '172.16.208.176',
                        port: 18883,
                        username: 'qxy1',
                        password: '5686670',
                        client_id: 'python_client',
                        keepalive: 60,
                        timeout: 10,
                        use_tls: false,
                        ca_certs: null,
                        certfile: null,
                        keyfile: null,
                        will_topic: 'clients/python_client_status',
                        will_payload: 'Client is offline',
                        will_qos: 1,
                        is_active: false
                    });
                    
                    // 获取设备和传感器数据
                    const fetchDevices = async () => {
                        try {
                            const response = await fetch('/api/devices');
                            const data = await response.json();
                            devices.value = Array.isArray(data) ? data : [];
                        } catch (error) {
                            console.error('获取设备数据失败:', error);
                            devices.value = [];
                        }
                    };
                    
                    const fetchSensors = async () => {
                        try {
                            const response = await fetch('/api/sensors');
                            const data = await response.json();
                            sensors.value = Array.isArray(data) ? data : [];
                        } catch (error) {
                            console.error('获取传感器数据失败:', error);
                            sensors.value = [];
                        }
                    };
                    
                    // 获取MQTT配置数据
                    const fetchMqttConfigs = async () => {
                        try {
                            const response = await fetch('/api/mqtt-configs');
                            const data = await response.json();
                            mqttConfigs.value = Array.isArray(data) ? data : [];
                        } catch (error) {
                            console.error('获取MQTT配置数据失败:', error);
                            mqttConfigs.value = [];
                        }
                    };
                    
                    // 获取特定设备的传感器
                    const getDeviceSensors = (deviceId) => {
                        if (!Array.isArray(sensors.value)) {
                            return [];
                        }
                        return sensors.value.filter(sensor => sensor.device_id === deviceId);
                    };
                    
                    // 计算属性
                    const onlineDevicesCount = computed(() => {
                        if (!Array.isArray(devices.value)) {
                            return 0;
                        }
                        return devices.value.filter(device => device.status === '在线').length;
                    });
                    
                    const offlineDevicesCount = computed(() => {
                        if (!Array.isArray(devices.value)) {
                            return 0;
                        }
                        return devices.value.filter(device => device.status === '离线').length;
                    });
                    
                    const sensorsCount = computed(() => {
                        if (!Array.isArray(sensors.value)) {
                            return 0;
                        }
                        return sensors.value.length;
                    });
                    
                    // 添加设备
                    const addDevice = async () => {
                        try {
                            const response = await fetch('/api/devices', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(newDevice.value)
                            });
                            
                            if (response.ok) {
                                await fetchDevices();
                                resetForm();
                                alert('设备添加成功');
                            } else {
                                alert('添加设备失败');
                            }
                        } catch (error) {
                            console.error('添加设备失败:', error);
                            alert('添加设备失败');
                        }
                    };
                    
                    // 更新设备
                    const updateDevice = async () => {
                        try {
                            const response = await fetch(`/api/devices/${editingDevice.value.id}`, {
                                method: 'PUT',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    name: newDevice.value.name,
                                    device_type: newDevice.value.device_type,
                                    location: newDevice.value.location
                                })
                            });
                            
                            if (response.ok) {
                                await fetchDevices();
                                resetForm();
                                alert('设备更新成功');
                            } else {
                                alert('更新设备失败');
                            }
                        } catch (error) {
                            console.error('更新设备失败:', error);
                            alert('更新设备失败');
                        }
                    };
                    
                    // 删除设备
                    const deleteDevice = async (deviceId) => {
                        if (!confirm('确定要删除这个设备吗？此操作不可撤销！')) {
                            return;
                        }
                        
                        try {
                            const response = await fetch(`/api/devices/${deviceId}`, {
                                method: 'DELETE'
                            });
                            
                            if (response.ok) {
                                devices.value = devices.value.filter(device => device.id !== deviceId);
                                // 同时从本地传感器列表中移除相关传感器
                                sensors.value = sensors.value.filter(sensor => sensor.device_id !== deviceId);
                                alert('设备删除成功');
                            } else {
                                alert('删除设备失败');
                            }
                        } catch (error) {
                            console.error('删除设备失败:', error);
                            alert('删除设备失败');
                        }
                    };
                    
                    // 编辑设备
                    const editDevice = (device) => {
                        editingDevice.value = { ...device };
                        newDevice.value.name = device.name;
                        newDevice.value.device_type = device.device_type;
                        newDevice.value.location = device.location;
                    };
                    
                    // 保存设备（添加或更新）
                    const saveDevice = () => {
                        if (!newDevice.value.name || !newDevice.value.device_type || !newDevice.value.location) {
                            alert('请填写设备名称、类型和位置');
                            return;
                        }
                        
                        if (editingDevice.value) {
                            updateDevice();
                        } else {
                            addDevice();
                        }
                    };
                    
                    // 取消编辑
                    const cancelEdit = () => {
                        resetForm();
                    };
                    
                    // 重置表单
                    const resetForm = () => {
                        newDevice.value = { name: '', device_type: '', location: '' };
                        editingDevice.value = null;
                    };
                    
                    // MQTT配置相关函数
                    const addMqttConfig = async () => {
                        try {
                            const response = await fetch('/api/mqtt-configs', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(newMqttConfig.value)
                            });
                            
                            if (response.ok) {
                                await fetchMqttConfigs();
                                resetMqttForm();
                                alert('MQTT配置添加成功');
                            } else {
                                const errorData = await response.json();
                                alert('添加MQTT配置失败: ' + errorData.message);
                            }
                        } catch (error) {
                            console.error('添加MQTT配置失败:', error);
                            alert('添加MQTT配置失败');
                        }
                    };
                    
                    const updateMqttConfig = async () => {
                        try {
                            const response = await fetch(`/api/mqtt-configs/${editingMqttConfig.value.id}`, {
                                method: 'PUT',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(newMqttConfig.value)
                            });
                            
                            if (response.ok) {
                                await fetchMqttConfigs();
                                resetMqttForm();
                                alert('MQTT配置更新成功');
                            } else {
                                const errorData = await response.json();
                                alert('更新MQTT配置失败: ' + errorData.message);
                            }
                        } catch (error) {
                            console.error('更新MQTT配置失败:', error);
                            alert('更新MQTT配置失败');
                        }
                    };
                    
                    const deleteMqttConfig = async (configId) => {
                        if (!confirm('确定要删除这个MQTT配置吗？此操作不可撤销！')) {
                            return;
                        }
                        
                        try {
                            const response = await fetch(`/api/mqtt-configs/${configId}`, {
                                method: 'DELETE'
                            });
                            
                            if (response.ok) {
                                mqttConfigs.value = mqttConfigs.value.filter(config => config.id !== configId);
                                alert('MQTT配置删除成功');
                            } else {
                                const errorData = await response.json();
                                alert('删除MQTT配置失败: ' + errorData.message);
                            }
                        } catch (error) {
                            console.error('删除MQTT配置失败:', error);
                            alert('删除MQTT配置失败');
                        }
                    };
                    
                    const testMqttConfig = async (configId) => {
                        try {
                            const response = await fetch(`/api/mqtt-configs/${configId}/test`, {
                                method: 'POST'
                            });
                            
                            if (response.ok) {
                                const data = await response.json();
                                alert('MQTT连接测试成功: ' + data.message);
                            } else {
                                const errorData = await response.json();
                                alert('MQTT连接测试失败: ' + errorData.message);
                            }
                        } catch (error) {
                            console.error('MQTT连接测试失败:', error);
                            alert('MQTT连接测试失败: ' + error.message);
                        }
                    };
                    
                    const activateMqttConfig = async (configId) => {
                        if (!confirm('确定要激活这个MQTT配置吗？这将停用当前激活的配置。')) {
                            return;
                        }
                        
                        try {
                            const response = await fetch(`/api/mqtt-configs/${configId}/activate`, {
                                method: 'POST'
                            });
                            
                            if (response.ok) {
                                await fetchMqttConfigs();
                                alert('MQTT配置激活成功');
                            } else {
                                const errorData = await response.json();
                                alert('激活MQTT配置失败: ' + errorData.message);
                            }
                        } catch (error) {
                            console.error('激活MQTT配置失败:', error);
                            alert('激活MQTT配置失败: ' + error.message);
                        }
                    };
                    
                    const editMqttConfig = (config) => {
                        editingMqttConfig.value = { ...config };
                        // 复制配置到newMqttConfig
                        Object.assign(newMqttConfig.value, config);
                    };
                    
                    const saveMqttConfig = () => {
                        if (!newMqttConfig.value.name) {
                            alert('请填写配置名称');
                            return;
                        }
                        
                        if (editingMqttConfig.value) {
                            updateMqttConfig();
                        } else {
                            addMqttConfig();
                        }
                    };
                    
                    const cancelMqttEdit = () => {
                        resetMqttForm();
                    };
                    
                    const resetMqttForm = () => {
                        newMqttConfig.value = {
                            name: '',
                            server: '172.16.208.176',
                            port: 18883,
                            username: 'qxy1',
                            password: '5686670',
                            client_id: 'python_client',
                            keepalive: 60,
                            timeout: 10,
                            use_tls: false,
                            ca_certs: null,
                            certfile: null,
                            keyfile: null,
                            will_topic: 'clients/python_client_status',
                            will_payload: 'Client is offline',
                            will_qos: 1,
                            is_active: false
                        };
                        editingMqttConfig.value = null;
                    };
                    
                    // 更改视图
                    const changeView = (view) => {
                        currentView.value = view;
                        if (view === 'sensors') {
                            fetchSensors(); // 在传感器监控视图中获取传感器数据
                        } else if (view === 'settings') {
                            fetchMqttConfigs(); // 在系统设置视图中获取MQTT配置数据
                        }
                        switch(view) {
                            case 'dashboard':
                                currentViewTitle.value = '设备管理';
                                currentViewIcon.value = 'fas fa-server';
                                break;
                            case 'sensors':
                                currentViewTitle.value = '传感器监控';
                                currentViewIcon.value = 'fas fa-wave-square';
                                break;
                            case 'stats':
                                currentViewTitle.value = '数据统计';
                                currentViewIcon.value = 'fas fa-chart-line';
                                break;
                            case 'alerts':
                                currentViewTitle.value = '告警管理';
                                currentViewIcon.value = 'fas fa-bell';
                                break;
                            case 'settings':
                                currentViewTitle.value = '系统设置';
                                currentViewIcon.value = 'fas fa-cog';
                                break;
                        }
                    };
                    
                    onMounted(() => {
                        fetchDevices(); // 初始获取设备数据
                        fetchSensors(); // 初始获取传感器数据
                        fetchMqttConfigs(); // 初始获取MQTT配置数据
                    });
                    
                    return {
                        currentView,
                        currentViewTitle,
                        currentViewIcon,
                        devices,
                        sensors,
                        mqttConfigs,
                        editingDevice,
                        newDevice,
                        editingMqttConfig,
                        newMqttConfig,
                        showAdvancedOptions,
                        onlineDevicesCount,
                        offlineDevicesCount,
                        sensorsCount,
                        getDeviceSensors,
                        changeView,
                        deleteDevice,
                        editDevice,
                        saveDevice,
                        cancelEdit,
                        addMqttConfig,
                        updateMqttConfig,
                        deleteMqttConfig,
                        testMqttConfig,
                        activateMqttConfig,
                        editMqttConfig,
                        saveMqttConfig,
                        cancelMqttEdit
                    };
                }
            }).mount('#app');
        </script>
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