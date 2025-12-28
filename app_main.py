from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_mapping(
        SECRET_KEY='dev_key_here',
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(os.getcwd(), "iot_system.db")}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    # 初始化扩展
    db = SQLAlchemy()
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # 注册蓝图
    from .auth import auth as auth_bp
    app.register_blueprint(auth_bp)
    
    from .main import main as main_bp
    app.register_blueprint(main_bp)
    
    # 将db和login_manager作为app的属性存储
    app.db = db
    app.login_manager = login_manager
    
    return app


def register_login_loader(app):
    from .models import User
    @app.login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))