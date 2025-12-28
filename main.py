from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required
import random


main = Blueprint('main', __name__)


@main.route('/')
def index():
    # 如果用户已登录，重定向到仪表板
    from flask_login import current_user
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