import threading
import time

import serial
import serial.tools.list_ports

from config import Config
from utils import dbHelper
from utils.dbHelper import get_r_standard_by_service_id
from utils.portHelper import get_return_msg
from utils.testResistanceHelper import get_r, open_door

"""
读卡器
02 + 卡号 +0D 0A 03
"""
# 用于防止并发刷卡
is_processing_enter = False
is_processing_leave = False
# 目标二进制数组
target_end_data = bytes([0x0D, 0x0A, 0x03])


def card_process(access_flag, _port, _baudrates, socketio=None):
    global is_processing_enter, is_processing_leave
    door = "进门" if access_flag == 1 else "出门"
    with serial.Serial(_port, _baudrates, timeout=Config.default_com_timeout) as ser:
        print(f"=================={door}读卡监听中==================")
        if socketio is None:
            print("socketio未开启")
        else:
            print("socketio已开启")
        # 循环监听读卡
        while True:
            time.sleep(0.001)
            buffer = get_return_msg(ser)
            global target_end_data
            # 读取到完整数据帧
            if len(buffer) > 4 and buffer[0] == 2 and buffer[-3:]:
                if access_flag == 1 and is_processing_enter:
                    # 打断前端过程
                    socketio.emit('repeat_card', {'status': access_flag})
                    print(f"=================={door}串口重复刷卡!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    time.sleep(1)
                if access_flag == 2 and is_processing_leave:
                    socketio.emit('repeat_card', {'status': access_flag})
                    print(f"=================={door}串口重复刷卡!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    time.sleep(1)
                is_processing_enter = True if access_flag == 1 else False
                is_processing_leave = True if access_flag == 2 else False
                hex_data_string = ' '.join(f'{byte:02X}' for byte in buffer)
                print(f"==================数据帧校验通过,{door}串口接收到的完整数据帧:", hex_data_string)
                # 获取卡号
                frame_data = buffer[1:-3]  # 将每个十六进制数转换为对应的 ASCII 字符
                ascii_chars_card = [chr(byte) for byte in frame_data]
                card_id = ''.join(ascii_chars_card)
                socketio.emit('read_card_status', {'status': access_flag})
                # 读取用户信息并处理
                user = dbHelper.get_user_by_card_id(card_id)
                if user:
                    handle_valid_card(user, card_id, access_flag, socketio)
                else:
                    handle_invalid_card(card_id, socketio)
                if access_flag == 1:
                    is_processing_enter = False
                else:
                    is_processing_leave = False
            buffer.clear()  # 清空缓冲区


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
    # 未检查该门禁与员工的权限关系
    service_id, value_hand_left, value_hand_right, value_foot_left, value_foot_right = get_r()
    hand_left_min, hand_left_max, hand_right_min, hand_right_max, foot_left_min, foot_left_max, foot_right_min, foot_right_max = get_r_standard_by_service_id(
        service_id)
    result_num = 0  # 0表示未成功，1表示成功

    def sent_success_data(second=None):
        global result_num
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
            result_num = 1
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
            'second': second
        }
        print(set_data)
        socketio.emit('success_data', {'data': set_data})
        print("发送success_data数据到前端")

    sent_success_data()
    if result_num == 1:
        print("人员及电阻均符合要求,通行")
        open_door()
    else:  # 失败则开始再次测试电阻，测试6s，每0.5s发送一次数据更新到前端
        total_duration = 6  # 测试的总时间为6秒
        interval = 0.5  # 每0.5秒测试一次
        remaining_time = total_duration  # 剩余时间

        def test_resistance_loop():
            nonlocal remaining_time
            if remaining_time <= 0:
                print("测试已完成")
                return  # 测试完成，退出循环
            # 每次测试并发送数据
            sent_success_data(remaining_time)
            # 减少剩余时间
            remaining_time -= interval
            # 0.5秒后再次调用自己
            threading.Timer(interval, test_resistance_loop).start()

        # 开始测试阻值
        test_resistance_loop()
