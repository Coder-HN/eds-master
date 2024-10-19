import logging
import threading
import time

from flask import Flask, request
from flask_socketio import SocketIO

from config import Config
from database import db
from router.router_admin_access import searchAccess
from router.router_admin_attend import searchAttend
from router.router_admin_manager_department import manageDepartment
from router.router_admin_manager_service import manageService
from router.router_admin_manager_user import manageUser
from router.router_user import user
from utils.readCardHelper import enter_card_process, leave_card_process

# 锁用于防止并发刷卡
enter_lock = threading.Lock()
leave_lock = threading.Lock()
is_processing_enter = False
is_processing_leave = False
get_except_enter = False
get_except_leave = False


# 进门串口
def enter_connect_socket(socketio):
    baudrates = Config.default_baudrates
    port_enter = Config.test_enter_card_port

    while True:
        with enter_lock:
            global is_processing_enter
            if not is_processing_enter:
                try:
                    # 处理刷卡逻辑
                    enter_card_process(port_enter, baudrates, socketio)
                    is_processing_enter = True  # 标记刷卡处理中
                    global get_except_enter
                    get_except_enter = False
                except Exception as e:
                    if not get_except_enter:
                        print(f"进门串口错误: {e}")
                        get_except_enter = True
                    socketio.emit('card_process', {'status': 'error', 'message': f'进门串口错误: {e}'})  # 在视频页面监听
            elif not get_except_enter:
                # 发送重复刷卡信息到前端
                print("进门重复刷卡，忽略此次刷卡")
                socketio.emit('card_process', {'status': 'error', 'message': '请勿重复刷卡'})
        time.sleep(0.5)


# 出门串口
def leave_connect_socket(socketio):
    baudrates = Config.default_baudrates
    port_leave = Config.test_leave_card_port
    while True:
        with leave_lock:
            global is_processing_leave
            if not is_processing_leave:
                try:
                    # 处理刷卡逻辑
                    leave_card_process(port_leave, baudrates, socketio)
                    is_processing_leave = True  # 标记刷卡处理中
                    global get_except_leave
                    get_except_leave = False
                except Exception as e:
                    if not get_except_enter:
                        print(f"出门串口错误: {e}")
                        get_except_leave = True
                    socketio.emit('card_process', {'status': 'error', 'message': f'出门串口错误: {e}'})
            elif not get_except_leave:
                # 发送重复刷卡信息到前端
                print("出门重复刷卡，忽略此次刷卡")
                socketio.emit('card_process', {'status': 'error', 'message': '请勿重复刷卡'})
        time.sleep(0.5)


# 使用配置文件配置数据库配置
def create_app(config_class=Config):
    _app = Flask(__name__)
    _app.config.from_object(config_class)

    # 串口IO
    socketio = SocketIO(_app, cors_allowed_origins="*", logger=False, engineio_logger=False)
    thread_enter = threading.Thread(target=enter_connect_socket, args=(socketio,))
    thread_enter.daemon = True
    thread_enter.start()
    thread_leave = threading.Thread(target=leave_connect_socket, args=(socketio,))
    thread_leave.daemon = True
    thread_leave.start()

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


# pycharm调试乱码可以用以下代码解决
# if hasattr(sys.stdout, 'reconfigure'):
#     sys.stdout.reconfigure(encoding='utf-8')
# else:
#     # 对于不支持 reconfigure 的情况，手动设置编码
#     sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
#     sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
