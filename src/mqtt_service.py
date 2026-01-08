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

    def subscribe_to_topics(self):
        """订阅主题"""
        # 重新获取激活的主题配置
        if self.db:
            self.topic_config = get_active_topic_config(self.db)
        
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

    def unsubscribe_from_topics(self):
        """取消订阅所有主题"""
        # 重新获取激活的主题配置
        if self.db:
            self.topic_config = get_active_topic_config(self.db)
        
        if not self.client or not self.topic_config:
            print("MQTT客户端或主题配置未初始化")
            return

        try:
            # 解析订阅主题列表
            topics = self.parse_topics(self.topic_config.subscribe_topics)
            
            for topic in topics:
                self.client.unsubscribe(topic)
                print(f"已取消订阅主题: {topic}")
        except Exception as e:
            print(f"取消订阅主题失败: {e}")

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
        print(f"处理传感器数据，Topic: {topic}, Payload: {payload}")
        
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
        
        # 尝试通过topic创建传感器数据
        self.process_topic_based_sensor_data(payload, topic)
        
        # 从主题中提取设备信息
        # 主题格式应为 "prefix/device_name" 或 "prefix/device_id"，例如 "stm32/1" 或 "devices/stm32"
        parts = topic.split('/')
        if len(parts) < 2:
            print(f"主题格式不正确，跳过处理: {topic}")
            return
        
        # 尝试从数据库中查找设备
        # 处理不同的topic格式，如 "stm32/2" -> "stm32_2"
        device_prefix = parts[0]  # 例如 'stm32'
        device_id = parts[1]      # 例如 '2'
        
        # 尝试多种匹配策略
        potential_device_names = [
            f"{device_prefix}_{device_id}",  # 如 "stm32_2"
            device_id,                       # 如 "2"
            device_prefix,                   # 如 "stm32"
            f"{device_prefix}/{device_id}"   # 如 "stm32/2"
        ]
        
        device = None
        device_name = None
        for potential_name in potential_device_names:
            device = self.db.query(DeviceModel).filter(DeviceModel.name == potential_name).first()
            if device:
                device_name = potential_name
                print(f"找到设备: {device_name} (通过匹配 '{potential_name}')")
                break
        
        # 如果以上策略都失败，尝试模糊匹配
        if not device:
            # 尝试查找包含前缀的设备
            device = self.db.query(DeviceModel).filter(DeviceModel.name.like(f'%{device_prefix}%')).first()
            if device:
                device_name = device.name
                print(f"找到设备: {device_name} (通过模糊匹配)")
        
        # 如果仍然没找到，使用原始topic作为设备名
        if not device:
            device_name = f"{device_prefix}_{device_id}"  # 使用下划线格式
            print(f"未找到现有设备，将使用新设备名: {device_name}")
        
        # 检查设备名称是否有效（允许字母数字组合）
        if not device_name or len(device_name) <= 1:
            print(f"设备名称无效，跳过创建设备: {device_name}")
            return
        
        try:
            # 查找设备，如果不存在则自动创建
            device = self.db.query(DeviceModel).filter(DeviceModel.name == device_name).first()
            if not device:
                print(f"设备 {device_name} 不存在，自动创建...")
                device = DeviceModel(
                    name=device_name,
                    device_type="自动创建设备",
                    status="在线",
                    location="未知位置"
                )
                self.db.add(device)
                self.db.commit()
                self.db.refresh(device)  # 刷新以获取新分配的ID
                print(f"已创建设备: {device_name}，ID: {device.id}")
            else:
                print(f"使用现有设备: {device_name}，ID: {device.id}")
            
            # 保存传感器数据
            if temp1_match:
                value = float(temp1_match.group(1))
                print(f"保存Temperature1: {value}")
                self.save_sensor_data(self.db, device.id, "Temperature1", value, "°C")
            if hum1_match:
                value = float(hum1_match.group(1))
                print(f"保存Humidity1: {value}")
                self.save_sensor_data(self.db, device.id, "Humidity1", value, "%")
            if temp2_match:
                value = float(temp2_match.group(1))
                print(f"保存Temperature2: {value}")
                self.save_sensor_data(self.db, device.id, "Temperature2", value, "°C")
            if hum2_match:
                value = float(hum2_match.group(1))
                print(f"保存Humidity2: {value}")
                self.save_sensor_data(self.db, device.id, "Humidity2", value, "%")
            if relay_match:
                value = int(relay_match.group(1))
                print(f"保存Relay Status: {value}")
                self.save_sensor_data(self.db, device.id, "Relay Status", value, "")
            if pb8_match:
                value = int(pb8_match.group(1))
                print(f"保存PB8 Level: {value}")
                self.save_sensor_data(self.db, device.id, "PB8 Level", value, "")
            
            self.db.commit()
            print(f"传感器数据已提交到数据库")
        except Exception as e:
            print(f"保存传感器数据时出错: {e}")
            self.db.rollback()

    def process_topic_based_sensor_data(self, payload, topic):
        """根据topic结构处理传感器数据"""
        print(f"处理基于Topic的传感器数据，Topic: {topic}, Payload: {payload}")
        # 从主题中提取设备信息和传感器类型
        # 支持多种主题格式，如:
        # - "device/1/temperature" -> 设备ID为1，传感器类型为temperature
        # - "stm32/2" -> 设备名stm32/2，传感器类型从payload中解析
        # - "sensors/room1/temperature" -> 设备名为room1，传感器类型为temperature
        
        parts = topic.split('/')
        if len(parts) < 2:
            print(f"主题格式不正确，跳过处理: {topic}")
            return

        # 根据topic格式处理数据
        if len(parts) >= 3:
            # 格式如 "sensors/device_name/sensor_type"
            device_name = parts[1]
            sensor_type = parts[2]
            
            print(f"检测到3段式Topic: 设备名={device_name}, 传感器类型={sensor_type}")
            
            # 尝试从payload中解析数值
            try:
                value = float(payload)
                self.create_or_update_sensor_data(device_name, sensor_type, value, topic)
            except ValueError:
                # 如果payload不是数值，尝试解析JSON格式
                try:
                    data = json.loads(payload)
                    if 'value' in data:
                        self.create_or_update_sensor_data(device_name, sensor_type, data['value'], topic, 
                                                          unit=data.get('unit', ''))
                    elif len(data) == 1:
                        # 如果JSON只有一个键值对，使用键作为传感器类型，值作为数值
                        key, value = next(iter(data.items()))
                        if isinstance(value, (int, float)):
                            self.create_or_update_sensor_data(device_name, key, value, topic)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，尝试提取数值
                    number_match = re.search(r'[\d.]+', payload)
                    if number_match:
                        value = float(number_match.group())
                        self.create_or_update_sensor_data(device_name, sensor_type, value, topic)
        elif len(parts) == 2:
            # 格式如 "stm32/2" 或 "device/1"
            device_prefix = parts[0]  # 例如 "stm32"
            device_id = parts[1]      # 例如 "2"
            device_name = f"{device_prefix}/{device_id}"  # 例如 "stm32/2"
            
            print(f"检测到2段式Topic: 设备名={device_name}, 原始payload={payload}")
            
            # 检查数据库中是否已存在这样的设备名
            existing_device = self.db.query(DeviceModel).filter(DeviceModel.name == device_name).first()
            if existing_device:
                print(f"找到已存在的设备: {device_name}, ID: {existing_device.id}")
                # 如果数据库中已存在"stm32/2"这样的设备，则直接使用
                self.parse_payload_for_device(device_name, payload, topic)
            else:
                # 如果不存在，尝试查找匹配的设备，如"stm32_2"
                # 需要将"stm32/2"转换为可能的数据库存储格式，如"stm32_2"
                potential_device_names = [
                    f"{device_prefix}_{device_id}",  # stm32_2
                    device_id,                       # 2
                    device_prefix                    # stm32
                ]
                
                found_device = False
                for potential_name in potential_device_names:
                    existing_device = self.db.query(DeviceModel).filter(DeviceModel.name == potential_name).first()
                    if existing_device:
                        print(f"找到设备: {potential_name}, ID: {existing_device.id}")
                        self.parse_payload_for_device(potential_name, payload, topic)
                        found_device = True
                        break
                
                if not found_device:
                    print(f"未找到设备 {device_name} 或其变体，将创建新设备")
                    self.parse_payload_for_device(device_name, payload, topic)
        else:
            print(f"主题格式不支持: {topic}")

    def parse_payload_for_device(self, device_name, payload, topic):
        """解析payload并为指定设备创建传感器数据"""
        print(f"解析设备 {device_name} 的payload: {payload}")
        
        # 查找或创建设备
        device = self.db.query(DeviceModel).filter(DeviceModel.name == device_name).first()
        if not device:
            print(f"设备 {device_name} 不存在，自动创建...")
            device = DeviceModel(
                name=device_name,
                device_type="自动创建设备",
                status="在线",
                location="未知位置"
            )
            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)  # 刷新以获取新分配的ID
            print(f"已创建设备: {device_name}, ID: {device.id}")
        else:
            print(f"使用现有设备: {device_name}, ID: {device.id}")
        
        # 使用正则表达式解析传感器数据
        # 匹配格式如 "Temperature1: 22.10 C, Humidity1: 16.10 %"
        # 或者 "Temperature1: 22.10 C\nHumidity1: 16.10 %"
        
        # 匹配各种传感器数据格式
        patterns = [
            (r'Temperature1:\s*([\d.]+)\s*C', 'Temperature1', '°C'),
            (r'Humidity1:\s*([\d.]+)\s*%', 'Humidity1', '%'),
            (r'Temperature2:\s*([\d.]+)\s*C', 'Temperature2', '°C'),
            (r'Humidity2:\s*([\d.]+)\s*%', 'Humidity2', '%'),
            (r'Relay Status:\s*(\d)', 'Relay Status', ''),
            (r'PB8 Level:\s*(\d)', 'PB8 Level', ''),
        ]
        
        for pattern, sensor_type, unit in patterns:
            match = re.search(pattern, payload)
            if match:
                try:
                    value = float(match.group(1)) if unit != '' else int(match.group(1))
                    print(f"解析到传感器数据: {sensor_type} = {value} {unit}")
                    self.save_sensor_data(self.db, device.id, sensor_type, value, unit)
                except ValueError as e:
                    print(f"转换数值失败: {match.group(1)}, 错误: {e}")
        
        # 如果没有匹配到已知格式，尝试解析为简单数值
        if not any(re.search(pattern[0], payload) for pattern in patterns):
            # 尝试直接解析为数值
            number_matches = re.findall(r'([\d.]+)\s*([CF%]?)', payload)
            if number_matches:
                for value_str, unit in number_matches:
                    try:
                        value = float(value_str)
                        # 简单地使用topic作为传感器类型名
                        sensor_type = f"Sensor_{len(number_matches)}"
                        print(f"从数值解析: {sensor_type} = {value} {unit}")
                        self.save_sensor_data(self.db, device.id, sensor_type, value, unit)
                    except ValueError as e:
                        print(f"转换简单数值失败: {value_str}, 错误: {e}")
        
        # 提交更改
        self.db.commit()

    def create_or_update_sensor_data(self, device_name, sensor_type, value, topic, unit=''):
        """根据设备名、传感器类型和值创建或更新传感器数据"""
        try:
            print(f"尝试创建或更新传感器数据: 设备={device_name}, 类型={sensor_type}, 值={value}")
            
            # 查找设备，如果不存在则自动创建
            device = self.db.query(DeviceModel).filter(DeviceModel.name == device_name).first()
            if not device:
                print(f"设备 {device_name} 不存在，自动创建...")
                device = DeviceModel(
                    name=device_name,
                    device_type="自动创建设备",
                    status="在线",
                    location="未知位置"
                )
                self.db.add(device)
                self.db.commit()
                self.db.refresh(device)  # 刷新以获取新分配的ID
                print(f"已创建设备: {device_name}, ID: {device.id}")
            
            # 保存传感器数据
            self.save_sensor_data(self.db, device.id, sensor_type, value, unit)
            self.db.commit()
            print(f"已保存传感器数据: 设备={device_name}, 类型={sensor_type}, 值={value}")
        except Exception as e:
            print(f"创建或更新传感器数据时出错: {e}")
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
            # 先取消订阅当前主题
            self.unsubscribe_from_topics()
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