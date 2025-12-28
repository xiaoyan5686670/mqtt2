def get_devices_data():
    # 模拟获取设备数据，实际应用中应从数据库或MQTT订阅中获取
    devices = [
        {
            'id': 1,
            'name': '实验室设备A',
            'status': '在线',
            'location': '实验室1'
        },
        {
            'id': 2,
            'name': '实验室设备B',
            'status': '在线',
            'location': '实验室2'
        },
        {
            'id': 3,
            'name': '环境监测站C',
            'status': '离线',
            'location': '实验室3'
        }
    ]
    return devices