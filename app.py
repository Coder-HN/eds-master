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
from thread_tasks import monitor_entrance, monitor_exit, manage_system, electric_control


# 使用配置文件配置数据库配置
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # 初始化 SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
    print("==================socketio未开启" if socketio else "==================socketio已开启")

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
    # 初始化数据库
    db.init_app(app)
    with app.app_context():
        db.create_all()
    # 注册蓝图
    blueprints = [user, inter, manageUser, manageDepartment, manageService, searchAccess, searchAttend]
    for bp in blueprints:
        app.register_blueprint(bp)
    return app


"""
# 调试乱码用以下代码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    # 对于不支持 reconfigure 的情况，手动设置编码
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
"""
