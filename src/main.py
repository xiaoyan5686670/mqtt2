import os
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from fastapi import BackgroundTasks

# 导入各模块
from .database import SessionLocal, engine
from .models import Base, Device, MQTTConfig, TopicConfig, SensorData, SensorDataModel
from . import db_operations as db_ops
from . import mqtt_service

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
    devices = db_ops.get_devices(db, skip=skip, limit=limit)
    return devices


@app.get("/api/devices/{device_id}", response_model=Device)
async def get_device_api(device_id: int, db: Session = Depends(get_db)):
    device = db_ops.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.post("/api/devices", response_model=Device)
async def create_device_api(device: Device, db: Session = Depends(get_db)):
    db_device = db_ops.get_device_by_name(db, device.name)
    if db_device:
        raise HTTPException(status_code=400, detail="Device already exists")
    device_data = device.model_dump()
    result = db_ops.create_device(db, device_data)
    return result


@app.put("/api/devices/{device_id}", response_model=Device)
async def update_device_api(device_id: int, device: Device, db: Session = Depends(get_db)):
    device_data = device.model_dump()
    result = db_ops.update_device(db, device_id, device_data)
    if not result:
        raise HTTPException(status_code=404, detail="Device not found")
    return result


@app.delete("/api/devices/{device_id}")
async def delete_device_api(device_id: int, db: Session = Depends(get_db)):
    success = db_ops.delete_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deleted successfully"}


@app.get("/api/devices/{device_id}/history", response_model=List[dict])
async def get_device_history_api(device_id: int, db: Session = Depends(get_db)):
    history = db_ops.get_device_history_from_db(db, device_id)
    # 将SQLAlchemy模型转换为字典
    return [h.__dict__ for h in history if h]


@app.get("/api/realtime-sensors")
async def get_realtime_sensors_api(db: Session = Depends(get_db)):
    """获取实时传感器数据"""
    try:
        # 获取所有传感器的最新数据
        all_sensors = db_ops.get_all_sensors_from_db(db)
        
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
        latest_sensors = db_ops.get_latest_sensors_from_db(db)
        
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
    configs = db_ops.get_mqtt_configs(db, skip=skip, limit=limit)
    return configs


@app.get("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def get_mqtt_config_api(config_id: int, db: Session = Depends(get_db)):
    config = db_ops.get_mqtt_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return config


@app.post("/api/mqtt-configs", response_model=MQTTConfig)
async def create_mqtt_config_api(config: MQTTConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = db_ops.create_mqtt_config(db, config_data)
    return result


@app.put("/api/mqtt-configs/{config_id}", response_model=MQTTConfig)
async def update_mqtt_config_api(config_id: int, config: MQTTConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = db_ops.update_mqtt_config(db, config_id, config_data)
    if not result:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return result


@app.delete("/api/mqtt-configs/{config_id}")
async def delete_mqtt_config_api(config_id: int, db: Session = Depends(get_db)):
    success = db_ops.delete_mqtt_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="MQTT Config not found")
    return {"message": "MQTT Config deleted successfully"}


# 主题配置相关API
@app.get("/api/topic-configs", response_model=List[TopicConfig])
async def get_topic_configs_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    configs = db_ops.get_topic_configs(db, skip=skip, limit=limit)
    return configs


@app.get("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def get_topic_config_api(config_id: int, db: Session = Depends(get_db)):
    config = db_ops.get_topic_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return config


@app.post("/api/topic-configs", response_model=TopicConfig)
async def create_topic_config_api(config: TopicConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = db_ops.create_topic_config(db, config_data)
    return result


@app.put("/api/topic-configs/{config_id}", response_model=TopicConfig)
async def update_topic_config_api(config_id: int, config: TopicConfig, db: Session = Depends(get_db)):
    config_data = config.model_dump()
    result = db_ops.update_topic_config(db, config_id, config_data)
    if not result:
        raise HTTPException(status_code=404, detail="Topic Config not found")
    return result


@app.delete("/api/topic-configs/{config_id}")
async def delete_topic_config_api(config_id: int, db: Session = Depends(get_db)):
    success = db_ops.delete_topic_config(db, config_id)
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
    mqtt_service.start_mqtt_service()
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
