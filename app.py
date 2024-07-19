from flask import Flask
from config import Config
from database import db
from router.router_admin import admin
from router.router_user import user


def create_app(config_class=Config):
    _app = Flask(__name__)
    _app.config.from_object(config_class)
    # 初始化数据库
    db.init_app(_app)
    # 注册蓝图
    _app.register_blueprint(user)
    _app.register_blueprint(admin)
    return _app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
