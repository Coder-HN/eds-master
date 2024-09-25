import logging
import threading

from flask import Flask, request
from flask_socketio import SocketIO

from config import Config
from database import db
from router.router_admin_access import searchAccess
from router.router_admin_attend import searchAttend
from router.router_admin_manager_service import manageService
from router.router_admin_manager_user import manageUser
from router.router_user import user
from utils.readCardHelper import enter_card_process, leave_card_process


def enter_connect_socket(socketio):
    baudrates = Config.default_baudrates
    # 开门
    port_enter = Config.test_enter_card_port
    if port_enter is None:
        print(f"进门读卡串口{port_enter}未找到，请检查设备连接。")
    else:
        enter_card_process(port_enter, baudrates, socketio)


def leave_connect_socket(socketio):
    baudrates = Config.default_baudrates
    # 关门
    port_leave = Config.test_leave_card_port
    if port_leave is None:
        print(f"出门读卡串口{port_leave}未找到，请检查设备连接。")
    else:
        leave_card_process(port_leave, baudrates, socketio)


# 使用配置文件配置数据库配置
def create_app(config_class=Config):
    _app = Flask(__name__)
    _app.config.from_object(config_class)

    # 在请求处理之前记录请求信息
    @_app.before_request
    def log_request_info():
        _app.logger.info(f"Request: {request.method} {request.url}")

    # 在请求处理之后记录响应信息
    @_app.after_request
    def log_response_info(response):
        _app.logger.info(f"Response Status: {response.status}")
        return response

    # 清除所有已有的处理器
    for handler in _app.logger.handlers[:]:
        _app.logger.removeHandler(handler)
    # 配置日志记录
    _app.logger.setLevel(logging.INFO)
    # 创建一个格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    # 创建一个文件处理器并设置格式
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    _app.logger.addHandler(file_handler)

    # 串口IO
    socketio = SocketIO(_app, cors_allowed_origins="*")
    thread_enter = threading.Thread(target=enter_connect_socket, args=(socketio,))
    thread_enter.daemon = True
    thread_enter.start()
    thread_leave = threading.Thread(target=leave_connect_socket, args=(socketio,))
    thread_leave.daemon = True
    thread_leave.start()

    # 初始化数据库
    db.init_app(_app)

    # 注册蓝图
    _app.register_blueprint(user)
    _app.register_blueprint(manageUser)
    _app.register_blueprint(manageService)
    _app.register_blueprint(searchAccess)
    _app.register_blueprint(searchAttend)
    return _app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
