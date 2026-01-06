import requests
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试API端点
BASE_URL = "http://localhost:8000"

def test_devices_api():
    """测试获取设备列表API"""
    try:
        response = requests.get(f"{BASE_URL}/api/devices")
        print("设备列表API响应:")
        print(response.status_code)
        print(response.json())
        return response.json()
    except Exception as e:
        print(f"获取设备列表失败: {e}")
        return None

def test_latest_sensors_api(device_id):
    """测试获取指定设备最新传感器数据API"""
    try:
        response = requests.get(f"{BASE_URL}/api/devices/{device_id}/latest-sensors")
        print(f"设备 {device_id} 最新传感器数据API响应:")
        print(response.status_code)
        print(response.json())
        return response.json()
    except Exception as e:
        print(f"获取设备 {device_id} 最新传感器数据失败: {e}")
        return None

if __name__ == "__main__":
    print("测试API端点...")
    
    # 首先获取设备列表
    devices = test_devices_api()
    
    if devices:
        # 对每个设备测试获取最新传感器数据
        for device in devices:
            test_latest_sensors_api(device['id'])
            print("-" * 50)