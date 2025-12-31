import paho.mqtt.client as mqtt
import json
import threading
import re
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
import sys
import os

# 修复相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from database import SessionLocal
from models import DeviceModel, SensorDataModel, MQTTConfigModel
from config_service import get_active_mqtt_config, get_active_topic_config


class MQTTService:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.active_config = None
        self.topic_config = None
        self.db: Optional[Session] = None

    def init_mqtt_client(self):
        """初始化MQTT客户端"""
        try:
            # 获取数据库连接
            self.db = SessionLocal()
            
            # 获取激活的主题配置
            self.topic_config = get_active_topic_config(self.db)
            if not self.topic_config:
                print("未找到激活的主题配置")
                return False

            # 获取关联的MQTT配置
            self.active_config = self.db.query(MQTTConfigModel).filter(
                MQTTConfigModel.id == self.topic_config.mqtt_config_id
            ).first()
            
            if not self.active_config:
                print(f"未找到ID为 {self.topic_config.mqtt_config_id} 的MQTT配置")
                return False

            # 创建MQTT客户端
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message

            # 设置用户名密码（如果有的话）
            if self.active_config.username and self.active_config.password:
                self.client.username_pw_set(
                    self.active_config.username, 
                    self.active_config.password
                )

            # 连接MQTT服务器
            self.client.connect(
                self.active_config.server, 
                self.active_config.port, 
                60
            )
            print(f"MQTT客户端初始化成功，连接到 {self.active_config.server}:{self.active_config.port}")
            return True
        except Exception as e:
            print(f"初始化MQTT客户端失败: {e}")
            return False

    def on_connect(self, client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            print("MQTT连接成功")
            self.is_connected = True
            # 订阅主题
            self.subscribe_to_topics()
        else:
            print(f"MQTT连接失败，返回码: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        print("MQTT连接断开")
        self.is_connected = False
        self.is_connected = False

    def subscribe_to_topics(self):
        """订阅主题"""
        if not self.client or not self.topic_config:
            print("MQTT客户端或主题配置未初始化")
            return

        try:
            # 解析订阅主题列表
            topics = self.parse_topics(self.topic_config.subscribe_topics)
            
            for topic in topics:
                self.client.subscribe(topic)
                print(f"已订阅主题: {topic}")
        except Exception as e:
            print(f"订阅主题失败: {e}")

    def parse_topics(self, topics_str: str) -> List[str]:
        """解析主题字符串为列表"""
        if not topics_str:
            return []
        
        try:
            # 尝试解析为JSON数组
            parsed = json.loads(topics_str)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            # 如果不是JSON格式，则按换行符或逗号分割
            if '\n' in topics_str:
                return [t.strip() for t in topics_str.split('\n') if t.strip()]
            else:
                return [t.strip() for t in topics_str.split(',') if t.strip()]
        
        return []

    def on_message(self, client, userdata, msg):
        """MQTT消息回调函数"""
        print(f"收到消息: {msg.topic} - {msg.payload.decode()}")
        
        try:
            # 解析传感器数据
            payload = msg.payload.decode()
            self.process_sensor_data(payload, msg.topic)
        except Exception as e:
            print(f"处理消息时出错: {e}")

    def save_message_to_db(self, topic: str, payload: str):
        """保存消息到数据库"""
        try:
            # 创建传感器数据记录
            sensor_data = SensorDataModel(
                device_id=0,  # 暂时使用0，后续可以关联到具体设备
                type="mqtt_message",  # 传感器类型
                value=payload,  # 消息内容
                timestamp=datetime.utcnow(),
                topic=topic  # 消息主题
            )
            
            # 保存到数据库
            self.db.add(sensor_data)
            self.db.commit()
            print(f"消息已保存到数据库: {topic}")
        except Exception as e:
            print(f"保存消息到数据库失败: {e}")
            self.db.rollback()

    def on_message(self, client, userdata, msg):
        """消息接收回调"""
        print(f"收到消息: {msg.topic} - {msg.payload.decode()}")
        try:
            # 将消息保存到数据库
            self.save_message_to_db(msg.topic, msg.payload.decode())
        except Exception as e:
            print(f"处理消息时出错: {e}")

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
        """启动MQTT服务"""
        if not self.client:
            if not self.init_mqtt_client():
                return False
                
        print("启动MQTT服务...")
        # 在单独的线程中启动循环
        self.client.loop_start()
        return True

    def stop(self):
        """停止MQTT服务"""
        if self.client:
            print("停止MQTT服务...")
            self.client.loop_stop()
            self.client.disconnect()
        
        if self.db:
            self.db.close()


# 创建全局MQTT服务实例
mqtt_service = MQTTService()


def start_mqtt_service():
    """启动MQTT服务"""
    return mqtt_service.start()


def stop_mqtt_service():
    """停止MQTT服务"""
    mqtt_service.stop()