import time

import serial
import serial.tools.list_ports

from config import Config
from utils import dbHelper
from utils.dbHelper import get_r_standard_by_service_id
from utils.testResistanceHelper import get_r, open_door

"""
读卡器
02 + 卡号 +0D 0A 03
"""
# 用于防止并发刷卡
is_processing_enter = True
is_processing_leave = True
# 目标二进制数组
target_end_data = bytes([0x0D, 0x0A, 0x03])


def card_process(access_flag, _port, _baudrates, socketio=None):
    global is_processing_enter, is_processing_leave
    door = "进门" if access_flag == 1 else "出门"
    frame_timeout_ms = Config.default_com_timeout
    with serial.Serial(_port, _baudrates, timeout=frame_timeout_ms / 1000) as ser:
        buffer = bytearray()  # 临时存储数据
        frame_started = False  # 标记数据帧是否已经开始
        start_time = time.time()  # 记录帧开始的时间
        print(f"=================={door}读卡监听中==================")
        if socketio is None:
            print("socketio未开启")
        else:
            print("socketio已开启")
        while True:
            time.sleep(0.001)
            if ser.in_waiting > 0:
                # 读取所有可用的数据
                data = ser.read(ser.in_waiting)
                for byte in data:
                    if not frame_started:
                        frame_started = True  # 标记帧开始
                        start_time = time.time()  # 记录开始时间
                    buffer.append(byte)  # 将接收到的字节加入缓冲区

            if frame_started and (time.time() - start_time) * 1000 >= frame_timeout_ms:
                is_processing = False
                if access_flag == 1 and is_processing_enter:
                    is_processing = True
                if access_flag == 2 and is_processing_leave:
                    is_processing = True
                if buffer and is_processing:
                    if access_flag == 1:
                        is_processing_enter = False
                    else:
                        is_processing_leave = False
                    hex_data_string = ' '.join(f'{byte:02X}' for byte in buffer)

                    print(f"=================={door}串口{frame_timeout_ms}ms接收到的完整数据帧:", hex_data_string)

                    frame_data = buffer[1:-3]
                    hex_card_string = ' '.join(f'{byte:02X}' for byte in frame_data)
                    print(f"Hex card_id: {hex_card_string}")
                    # 将每个十六进制数转换为对应的 ASCII 字符
                    ascii_chars_card = [chr(byte) for byte in frame_data]
                    # 将字符数组连接成字符串
                    card_id = ''.join(ascii_chars_card)
                    print("card_id:", card_id)
                    # 读取末尾桢
                    frame_end = buffer[-3:]
                    hex_end = ' '.join(f'{byte:02X}' for byte in frame_end)
                    print(f"Hex end: {hex_end}")
                    global target_end_data
                    if len(buffer) > 4 and buffer[0] == 2 and frame_end == target_end_data:
                        print("数据帧校验通过")
                        socketio.emit('read_card_status', {'status': access_flag})

                        # 读取用户信息并处理
                        user = dbHelper.get_user_by_card_id(card_id)
                        if user:
                            handle_valid_card(user, card_id, access_flag, socketio)
                        else:
                            handle_invalid_card(card_id, socketio)
                buffer.clear()  # 清空缓冲区
                frame_started = False  # 重置帧标记


def handle_valid_card(user, card_id, access_flag, socketio):
    user_num = user['num']
    user_name = user['name']
    user_department = None
    user_department_num = user['department_num']
    if user_department_num is not None:
        department = dbHelper.get_department_by_num(user_department_num)
        if department:
            user_department = department['department_name']

    user_employee_id = user['employee_id']
    user_pic_path = user['pic_path']
    if access_flag == 1:
        cache_data = {
            'access_flag': access_flag,
            'card_id': card_id,
            'user_num': user_num,
            'name': user_name,
            'employee_id': user_employee_id,
            'department': user_department,
            'pic_path': user_pic_path,
        }
        time.sleep(1)  # 等待前端监听
        print(cache_data)
        socketio.emit('cache_data', {'data': cache_data})
        print("发送cache_data数据到前端")
        process_enter_routine(user_num, card_id, access_flag, socketio)
    elif access_flag == 2:
        # TODO 出门无法获取service_id
        service_id = 1
        set_data = {
            'card_id': card_id,
            'access_flag': access_flag,
            'service_id': service_id,

            'user_num': user_num,
            'name': user_name,
            'employee_id': user_employee_id,
            'department': user_department,
            'pic_path': user_pic_path,
        }
        time.sleep(1)  # 等待跳转后页面开启监听
        print(set_data)
        socketio.emit('success_data', {'data': set_data})
        print("开门中...")
        open_door()


def handle_invalid_card(card_id, socketio):
    time.sleep(1)  # 等待前端监听
    print(f"card_id={card_id}无权限通过")
    error_data = {'error_message': f"该卡人员不在数据库中,card_id={card_id}"}
    socketio.emit('fail_data', {'data': error_data})


def process_enter_routine(user_num, card_id, access_flag, socketio):
    print("测试电阻中...")
    result = False
    service_id, value_hand_left, value_hand_right, value_foot_left, value_foot_right = get_r()
    if service_id:
        hand_left_min, hand_left_max, hand_right_min, hand_right_max, foot_left_min, foot_left_max, foot_right_min, foot_right_max = get_r_standard_by_service_id(
            service_id)

        result_hand_left = 2
        result_hand_right = 2
        result_foot_left = 2
        result_foot_right = 2

        if hand_left_min <= value_hand_left <= hand_left_max:
            result_hand_left = 1
        if hand_right_min <= value_hand_right <= hand_right_max:
            result_hand_right = 1
        if foot_left_min <= value_foot_left <= foot_left_max:
            result_foot_left = 1
        if foot_right_min <= value_foot_right <= foot_right_max:
            result_foot_right = 1

        if result_hand_left * result_hand_right * result_foot_left * result_foot_right == 1:
            result = True

        result_num = 1 if result else 2
        set_data = {
            'user_num': user_num,
            'access_flag': access_flag,
            'card_id': card_id,
            'service_id': service_id,

            'hand_left_min': hand_left_min,
            'hand_left_max': hand_left_max,
            'hand_right_min': hand_right_min,
            'hand_right_max': hand_right_max,
            'foot_left_min': foot_left_min,
            'foot_left_max': foot_left_max,
            'foot_right_min': foot_right_min,
            'foot_right_max': foot_right_max,

            'value_hand_left': value_hand_left,
            'value_hand_right': value_hand_right,
            'value_foot_left': value_foot_left,
            'value_foot_right': value_foot_right,
            'result_hand_left': result_hand_left,
            'result_hand_right': result_hand_right,
            'result_foot_left': result_foot_left,
            'result_foot_right': result_foot_right,

            'result_num': result_num,
        }
        print(set_data)
        socketio.emit('success_data', {'data': set_data})
        print("发送success_data数据到前端")
        if result:
            print("人员及电阻均符合要求,通行")
            open_door()
    else:
        print("该门禁此人员无权限通过")
        error_data = {'error_message': f"该门禁未录入数据库,card_id={card_id},service_id={service_id}"}
        socketio.emit('fail_data', {'data': error_data})
