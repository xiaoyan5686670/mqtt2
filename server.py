from flask import Flask, Blueprint, render_template, redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import json
import random
from datetime import datetime
import os


# 创建应用实例
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_mapping(
    SECRET_KEY='dev_key_here',
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(os.getcwd(), "iot_system.db")}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


# 定义模型
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 创建蓝图
auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.vue_dashboard'))
        else:
            from flask import flash
            flash('用户名或密码错误')
    
    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@main.route('/')
def index():
    # 如果用户已登录，重定向到仪表板
    if current_user.is_authenticated:
        return redirect(url_for('main.vue_dashboard'))
    return redirect(url_for('auth.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    # 传统的Jinja2渲染仪表板
    devices = get_devices_data()
    return render_template('dashboard.html', devices=devices)


@main.route('/vue-dashboard')
@login_required
def vue_dashboard():
    # 返回Vue 3界面
    return render_template('vue_dashboard.html')


@main.route('/api/devices')
@login_required
def api_devices():
    # 返回JSON格式的设备数据，用于前端更新
    devices = get_devices_data()
    return jsonify(devices)


def get_devices_data():
    # 模拟获取设备数据，实际应用中应从数据库或MQTT订阅中获取
    devices = [
        {
            'id': 1,
            'name': '传感器A01',
            'status': '在线',
            'temperature': round(random.uniform(20, 30), 1),
            'humidity': round(random.uniform(50, 70), 1),
            'location': '实验室1'
        },
        {
            'id': 2,
            'name': '传感器B02',
            'status': '在线',
            'temperature': round(random.uniform(20, 30), 1),
            'humidity': round(random.uniform(50, 70), 1),
            'location': '实验室2'
        },
        {
            'id': 3,
            'name': '传感器C03',
            'status': '离线',
            'temperature': 0,
            'humidity': 0,
            'location': '实验室3'
        }
    ]
    return devices


# 注册蓝图
app.register_blueprint(auth)
app.register_blueprint(main)


def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 创建默认用户（如果不存在）
        if not User.query.first():
            default_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@example.com'
            )
            db.session.add(default_user)
            db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)