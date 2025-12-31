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

from src.database import SessionLocal
from src.models import DeviceModel, SensorDataModel, MQTTConfigModel
from src.config_service import get_active_mqtt_config, get_active_topic_config


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

    def subscribe_to_topic(self, topic: str):
        """动态订阅指定主题"""
        if not self.client:
            print("MQTT客户端未初始化")
            return False

        try:
            # 订阅指定主题
            self.client.subscribe(topic)
            print(f"已订阅主题: {topic}")
            return True
        except Exception as e:
            print(f"订阅主题失败: {e}")
            return False

    def unsubscribe_from_topic(self, topic: str):
        """取消订阅指定主题"""
        if not self.client:
            print("MQTT客户端未初始化")
            return False

        try:
            # 取消订阅指定主题
            self.client.unsubscribe(topic)
            print(f"已取消订阅主题: {topic}")
            return True
        except Exception as e:
            print(f"取消订阅主题失败: {e}")
            return False

    def on_message(self, client, userdata, msg):
        """消息接收回调"""
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
        # 主题格式应为 "prefix/device_name" 或 "prefix/device_id"，例如 "stm32/1" 或 "devices/stm32"
        parts = topic.split('/')
        if len(parts) < 2:
            print(f"主题格式不正确，跳过处理: {topic}")
            return
        
        # 尝试从数据库中查找设备
        # 如果直接使用第二部分无法找到设备，则尝试将整个前缀作为设备名
        device_candidate_1 = parts[1]  # 例如 '1' 在 'stm32/1' 中
        device_candidate_2 = parts[0]  # 例如 'stm32' 在 'stm32/1' 中
        
        # 首先尝试使用第二部分作为设备名
        device = self.db.query(DeviceModel).filter(DeviceModel.name == device_candidate_1).first()
        if device:
            device_name = device_candidate_1
        else:
            # 如果没找到，尝试使用第一部分作为设备名
            device = self.db.query(DeviceModel).filter(DeviceModel.name == device_candidate_2).first()
            if device:
                device_name = device_candidate_2
            else:
                # 如果仍然没找到，尝试组合模式，例如 'stm32' 可能对应 'stm32/1' 这样的主题
                device = self.db.query(DeviceModel).filter(DeviceModel.name.like(f'%{device_candidate_2}%')).first()
                if device:
                    device_name = device.name
                else:
                    print(f"设备 {device_candidate_1} 或 {device_candidate_2} 不存在，跳过处理")
                    return

        # 检查设备名称是否有效（允许字母数字组合）
        if not device_name or len(device_name) <= 1:
            print(f"设备名称无效，跳过创建设备: {device_name}")
            return
        
        try:
            # 查找设备
            device = self.db.query(DeviceModel).filter(DeviceModel.name == device_name).first()
            if not device:
                print(f"设备 {device_name} 不存在，跳过处理")
                return  # 不再自动创建设备，需要用户手动创建
            
            # 保存传感器数据
            if temp1_match:
                self.save_sensor_data(self.db, device.id, "Temperature1", float(temp1_match.group(1)), "°C")
            if hum1_match:
                self.save_sensor_data(self.db, device.id, "Humidity1", float(hum1_match.group(1)), "%")
            if temp2_match:
                self.save_sensor_data(self.db, device.id, "Temperature2", float(temp2_match.group(1)), "°C")
            if hum2_match:
                self.save_sensor_data(self.db, device.id, "Humidity2", float(hum2_match.group(1)), "%")
            if relay_match:
                self.save_sensor_data(self.db, device.id, "Relay Status", int(relay_match.group(1)), "")
            if pb8_match:
                self.save_sensor_data(self.db, device.id, "PB8 Level", int(pb8_match.group(1)), "")
            
            self.db.commit()
        except Exception as e:
            print(f"保存传感器数据时出错: {e}")
            self.db.rollback()

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
            # 更新告警状态
            if 'Temperature' in sensor_type and float(value) > 28:
                existing_sensor.alert_status = 'alert' if float(value) > 30 else 'warning'
            elif 'Humidity' in sensor_type and float(value) > 65:
                existing_sensor.alert_status = 'alert' if float(value) > 70 else 'warning'
            else:
                existing_sensor.alert_status = 'normal'
        else:
            # 创建新的传感器数据
            # 确定默认的最小值和最大值
            min_value = 0.0
            max_value = 100.0
            if 'Temperature' in sensor_type:
                min_value = -40.0  # 常见温度传感器范围
                max_value = 80.0
            elif 'Humidity' in sensor_type:
                min_value = 0.0   # 湿度范围
                max_value = 100.0
            
            sensor_data = SensorDataModel(
                device_id=device_id,
                type=sensor_type,
                value=value,
                unit=unit,
                timestamp=datetime.utcnow(),
                min_value=min_value,
                max_value=max_value,
                alert_status="normal"
            )
            
            # 更新告警状态
            if 'Temperature' in sensor_type and float(value) > 28:
                sensor_data.alert_status = 'alert' if float(value) > 30 else 'warning'
            elif 'Humidity' in sensor_type and float(value) > 65:
                sensor_data.alert_status = 'alert' if float(value) > 70 else 'warning'
            else:
                sensor_data.alert_status = 'normal'
                
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