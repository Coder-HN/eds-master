import threading
from flask import Flask
from flask_socketio import SocketIO
from config import Config
from database import db
from router.router_admin_access import searchAccess
from router.router_admin_attend import searchAttend
from router.router_admin_manager_department import manageDepartment
from router.router_admin_manager_service import manageService
from router.router_admin_manager_user import manageUser
from router.router_user import user
from router.router_internet import inter
from scheduler_internet import start_scheduler_with_context
from thread_tasks import monitor_entrance, monitor_exit, manage_system, electric_control
from utils.loggingHelper import setup_logging, clean_old_logs


def create_app(config_class=Config):
    # 创建 Flask 应用
    app = Flask(__name__)
    app.config.from_object(config_class)
    # 日志配置
    setup_logging(app)
    clean_old_logs()

    # 初始化 SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
    # TODO
    print("SocketIO 初始化成功" if socketio else "SocketIO 初始化失败")
    app.logger.info("SocketIO 初始化成功" if socketio else "SocketIO 初始化失败")

    # 启动多线程任务
    def start_threads():
        threading.Thread(target=monitor_entrance, args=(Config.test_enter_card_port, Config.default_baud_rate),
                         daemon=True).start()
        threading.Thread(target=monitor_exit, args=(Config.test_leave_card_port, Config.default_baud_rate),
                         daemon=True).start()
        threading.Thread(target=manage_system, args=(socketio,), daemon=True).start()
        threading.Thread(target=electric_control, args=(Config.test_r_port, Config.default_baud_rate, app),
                         daemon=True).start()

    start_threads()

    # 启动定时任务
    start_scheduler_with_context()

    # 初始化数据库
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # 注册蓝图
    blueprints = [user, inter, manageUser, manageDepartment, manageService, searchAccess, searchAttend]
    for bp in blueprints:
        app.register_blueprint(bp)
    return app
