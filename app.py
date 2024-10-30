import codecs
import logging
import sys
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
from thread_tasks import monitor_entrance, monitor_exit, manage_system, electric_control


# 使用配置文件配置数据库配置
def create_app(config_class=Config):
    _app = Flask(__name__)
    _app.config.from_object(config_class)

    # 发送信息给前端的串口IO
    socketio = SocketIO(_app, cors_allowed_origins="*", logger=False, engineio_logger=False)
    if socketio is None:
        print("==================socketio未开启")
    else:
        print("==================socketio已开启")

    # 启动线程的逻辑
    def start_threads():
        threading.Thread(target=monitor_entrance, args=(Config.test_enter_card_port, Config.default_baud_rate),
                         daemon=True).start()
        threading.Thread(target=monitor_exit, args=(Config.test_leave_card_port, Config.default_baud_rate),
                         daemon=True).start()
        threading.Thread(target=manage_system, args=(socketio,), daemon=True).start()
        threading.Thread(target=electric_control, args=(Config.test_r_port, Config.default_baud_rate),
                         daemon=True).start()

    # 启动后台线程来处理刷卡逻辑
    start_threads()

    # 配置日志记录
    _app.logger.setLevel(logging.INFO)
    # 创建一个文件处理器并设置格式
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    # 将处理器添加到应用日志
    _app.logger.addHandler(file_handler)

    # 初始化数据库
    db.init_app(_app)

    # 注册蓝图
    _app.register_blueprint(user)
    _app.register_blueprint(manageUser)
    _app.register_blueprint(manageDepartment)
    _app.register_blueprint(manageService)
    _app.register_blueprint(searchAccess)
    _app.register_blueprint(searchAttend)
    return _app


# 调试乱码用以下代码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    # 对于不支持 reconfigure 的情况，手动设置编码
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
