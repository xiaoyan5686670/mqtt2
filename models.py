from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# 创建一个db实例，但不初始化 - 在应用创建后会设置app.db
db = SQLAlchemy()


# 模型将在app创建后动态定义
def define_models(db):
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(200), nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=True)
        
        def set_password(self, password):
            self.password = generate_password_hash(password)
        
        def check_password(self, password):
            return check_password_hash(self.password, password)

    class Device(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        status = db.Column(db.String(20), nullable=False)  # 在线/离线
        location = db.Column(db.String(200), nullable=True)
        last_seen = db.Column(db.DateTime, nullable=True)
        # 传感器数据存储为JSON格式
        sensor_data = db.Column(db.Text, nullable=True)
        
        def __repr__(self):
            return f'<Device {self.name}>'
        
        def to_dict(self):
            return {
                'id': self.id,
                'name': self.name,
                'status': self.status,
                'location': self.location,
                'last_seen': self.last_seen.isoformat() if self.last_seen else None,
                'sensor_data': self.sensor_data
            }
    
    # 将模型添加到当前模块的命名空间
    globals()['User'] = User
    globals()['Device'] = Device
    
    return User, Device