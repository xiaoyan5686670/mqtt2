from app import create_app, register_login_loader

app = create_app()
register_login_loader(app)

def init_db():
    """初始化数据库"""
    with app.app_context():
        # 重新定义模型
        from models import define_models
        User, Device = define_models(app.db)
        
        app.db.create_all()
        
        # 创建默认用户（如果不存在）
        from werkzeug.security import generate_password_hash
        if not User.query.first():
            default_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@example.com'
            )
            app.db.session.add(default_user)
            app.db.session.commit()

# 执行数据库初始化
init_db()

# 在应用上下文中初始化MQTT客户端
mqtt_handler = None
simulator = None

if __name__ == '__main__':
    with app.app_context():
        # 重新定义模型
        from models import define_models
        User, Device = define_models(app.db)
        
        # 初始化MQTT客户端
        from mqtt_client import MQTTHandler, SensorDataSimulator
        mqtt_handler = MQTTHandler()
        
        # 尝试连接MQTT代理
        if mqtt_handler.connect():
            mqtt_handler.start_loop()
            # 启动模拟数据生成器
            simulator = SensorDataSimulator(mqtt_handler)
            simulator.start()
            print("MQTT客户端已启动")
        else:
            print("无法连接到MQTT代理，启动模拟模式")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # 程序退出时停止MQTT客户端
        if mqtt_handler:
            mqtt_handler.stop_loop()
        if simulator:
            simulator.stop()