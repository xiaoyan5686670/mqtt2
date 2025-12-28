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
    
    # 在函数内创建 db 实例
    db = SQLAlchemy()
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    # 注册蓝图
    from auth import auth as auth_bp
    app.register_blueprint(auth_bp)
    
    from main import main as main_bp
    app.register_blueprint(main_bp)
    
    # 将db和login_manager作为app的属性存储
    app.db = db
    app.login_manager = login_manager
    
    # 定义模型
    from models import define_models
    define_models(db)
    
    return app


def init_db(app):
    """初始化数据库"""
    with app.app_context():
        app.db.create_all()
        
        # 创建默认用户（如果不存在）
        from models import User
        from werkzeug.security import generate_password_hash
        if not User.query.first():
            default_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@example.com'
            )
            app.db.session.add(default_user)
            app.db.session.commit()


def register_login_loader(app):
    @app.login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))