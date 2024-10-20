import logging
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
from utils.portHelper import set_hex_data, get_return_msg, printf_byte, crc8_check
from utils.readCardHelper import card_process
import serial
import serial.tools.list_ports


# 开门
def enter_connect_socket(socketio):
    baud_rate = Config.default_baud_rate
    port_enter = Config.test_enter_card_port
    try:
        # 检查测试电阻串口在线状态
        with serial.Serial(port_enter, baud_rate, timeout=1) as ser:
            # 你的串口通信代码
            set_hex_data(ser, Config.hex_test_online)
            received_data = get_return_msg(ser)
            printf_byte(received_data)
        # CRC校验
        if crc8_check(received_data) and bytearray.fromhex(Config.hex_test_online_success) == received_data:
            print("获取测试电阻串口在线状态成功")
        card_process(1, port_enter, baud_rate, socketio)
    except Exception as e:
        print(f"进门串口错误: {e}")
        error_data = {'error_message': f"进门串口错误: {e}"}
        socketio.emit('fail_data', {'data': error_data})
        print("已发送fail_data")


# 出门
def leave_connect_socket(socketio):
    baud_rate = Config.default_baud_rate
    port_leave = Config.test_leave_card_port
    try:
        card_process(2, port_leave, baud_rate, socketio)
    except Exception as e:
        print(f"出门串口错误: {e}")
        error_data = {'error_message': f"出门串口错误: {e}"}
        socketio.emit('fail_data', {'data': error_data})
        print("已发送fail_data")


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


# 调试乱码用以下代码
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
