import paho.mqtt.client as mqtt
import json
import threading
import re
from datetime import datetime
from sqlalchemy.orm import Session
import sys
import os

# 修复相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from database import SessionLocal
from models import DeviceModel, SensorDataModel
from config_service import get_active_mqtt_config, get_active_topic_config


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


def stop_mqtt_service():
    """停止MQTT服务"""
    mqtt_service.stop()