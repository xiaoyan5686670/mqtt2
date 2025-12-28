import paho.mqtt.client as mqtt
import json
import threading
import time
from flask import current_app


class MQTTHandler:
    def __init__(self, broker='localhost', port=1883):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"MQTT连接结果: {rc}")
        if rc == 0:
            print("MQTT连接成功")
            client.subscribe("iot/sensors/#")  # 订阅传感器主题
        else:
            print("MQTT连接失败")
    
    def on_message(self, client, userdata, msg):
        print(f"收到消息: {msg.topic} - {msg.payload.decode()}")
        try:
            # 解析传感器数据
            sensor_data = json.loads(msg.payload.decode())
            
            # 这里可以处理传感器数据并存储到数据库
            # 例如：更新设备状态、记录传感器读数等
            self.process_sensor_data(sensor_data)
        except json.JSONDecodeError:
            print("无法解析JSON数据")
    
    def process_sensor_data(self, data):
        # 处理传感器数据的逻辑
        # 例如：更新数据库中的设备状态和传感器值
        from app import create_app
        app = create_app()
        with app.app_context():
            from models import define_models
            User, Device = define_models(app.db)
            
            device = Device.query.filter_by(name=data.get('device_id')).first()
            if device:
                device.sensor_data = json.dumps(data)
                device.status = '在线'
            else:
                # 如果设备不存在，创建新设备
                device = Device(
                    name=data.get('device_id', 'Unknown'),
                    status='在线',
                    location=data.get('location', 'Unknown'),
                    sensor_data=json.dumps(data)
                )
                app.db.session.add(device)
            
            app.db.session.commit()
    
    def connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            return True
        except Exception as e:
            print(f"MQTT连接失败: {e}")
            return False
    
    def start_loop(self):
        self.client.loop_start()
    
    def stop_loop(self):
        self.client.loop_stop()
    
    def publish_message(self, topic, message):
        self.client.publish(topic, message)


# 用于测试的模拟传感器数据生成器
class SensorDataSimulator:
    def __init__(self, mqtt_handler):
        self.mqtt_handler = mqtt_handler
        self.running = False
        self.thread = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._simulate_data)
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _simulate_data(self):
        import random
        device_ids = ['传感器A01', '传感器B02', '传感器C03']
        
        while self.running:
            for device_id in device_ids:
                # 模拟传感器数据
                sensor_data = {
                    'device_id': device_id,
                    'temperature': round(random.uniform(20, 30), 1),
                    'humidity': round(random.uniform(50, 70), 1),
                    'location': '实验室1' if device_id == '传感器A01' else 
                               '实验室2' if device_id == '传感器B02' else '实验室3',
                    'timestamp': time.time()
                }
                
                # 发布模拟数据
                self.mqtt_handler.publish_message(
                    f"iot/sensors/{device_id}", 
                    json.dumps(sensor_data)
                )
            
            time.sleep(5)  # 每5秒发送一次数据