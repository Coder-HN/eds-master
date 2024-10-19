import logging
import threading
import time

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
from utils.readCardHelper import card_process
import serial
import serial.tools.list_ports

# 锁用于防止并发刷卡
enter_lock = threading.Lock()
leave_lock = threading.Lock()
is_processing_enter = False
is_processing_leave = False
get_except_enter = False
get_except_leave = False


# 通用串口连接处理函数
def connect_socket(socketio, process_type, port, baud_rate, lock, is_processing_flag, get_except_flag):
    while True:
        with lock:
            if not is_processing_flag[0]:
                try:
                    # 打开串行端口
                    frame_timeout_ms = Config.default_com_timeout
                    with serial.Serial(port, baud_rate, timeout=frame_timeout_ms / 1000) as ser:
                        buffer = bytearray()  # 临时存储数据
                        frame_started = False  # 标记数据帧是否已经开始
                        start_time = time.time()  # 记录帧开始的时间
                        print(
                            f"=================={'进门' if process_type == 1 else '出门'}读卡监听中==================")

                        # 检查socketio连接
                        if socketio is None:
                            print("socketio未开启")
                        else:
                            print("socketio已开启")

                        while True:
                            time.sleep(0.001)
                            if ser.in_waiting > 0:
                                # 读取所有可用的数据
                                data = ser.read(ser.in_waiting)
                                # 遍历每个字节
                                for byte in data:
                                    if not frame_started:
                                        frame_started = True  # 标记帧开始
                                        start_time = time.time()  # 记录开始时间
                                    buffer.append(byte)  # 将接收到的字节加入缓冲区

                            # 检查是否已经超过帧超时时间（frame_timeout_ms 毫秒）
                            if frame_started and (time.time() - start_time) * 1000 >= frame_timeout_ms:
                                card_process(buffer, process_type, socketio, frame_timeout_ms)
                                buffer.clear()  # 清空缓冲区
                                frame_started = False  # 重置帧标记

                    is_processing_flag[0] = True  # 标记刷卡处理中
                    get_except_flag[0] = False
                except Exception as e:
                    if not get_except_flag[0]:
                        print(f"{'进门' if process_type == 1 else '出门'}串口错误: {e}")
                        get_except_flag[0] = True
                    socketio.emit('card_process', {'status': 'error',
                                                   'message': f"{'进门' if process_type == 1 else '出门'}串口错误: {e}"})
            else:
                # 发送重复刷卡信息到前端
                if not get_except_flag[0]:
                    print(f"{'进门' if process_type == 1 else '出门'}重复刷卡，忽略此次刷卡")
                    socketio.emit('card_process', {'status': 'error', 'message': '请勿重复刷卡'})
        time.sleep(0.5)


# 使用配置文件配置数据库配置
def create_app(config_class=Config):
    _app = Flask(__name__)
    _app.config.from_object(config_class)

    # 串口IO
    baud_rate = Config.default_baud_rate
    socketio = SocketIO(_app, cors_allowed_origins="*", logger=False, engineio_logger=False)
    # 启动进门串口线程
    thread_enter = threading.Thread(target=connect_socket, args=(
        socketio, 1, Config.test_enter_card_port, baud_rate, enter_lock, [is_processing_enter], [get_except_enter]))
    thread_enter.daemon = True
    thread_enter.start()
    # 启动出门串口线程
    thread_leave = threading.Thread(target=connect_socket, args=(
        socketio, 2, Config.test_leave_card_port, baud_rate, leave_lock, [is_processing_leave], [get_except_leave]))
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
