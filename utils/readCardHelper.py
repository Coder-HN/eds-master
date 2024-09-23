import time

import serial
import serial.tools.list_ports

from config import Config
from utils import dbHelper
from utils.portHelper import turn_16_to_10
from utils.testResistanceHelper import get_r, open_door

"""
读卡器
02 + 卡号 +0D 0A 03
"""
# 目标二进制数组
target_end_data = bytes([0x0D, 0x0A, 0x03])


# 整个读卡进门access_flag=1，测试电阻过程
def enter_card_process(_port, _baudrates, socketio=None):
    try:
        # 打开串行端口
        frame_timeout_ms = Config.default_com_timeout
        with serial.Serial(_port, _baudrates, timeout=frame_timeout_ms / 1000) as ser:
            buffer = bytearray()  # 临时存储数据
            frame_started = False  # 标记数据帧是否已经开始
            start_time = time.time()  # 记录帧开始的时间
            print("进门读卡中...")
            while True:
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
                    if buffer:
                        hex_data_string = ' '.join(f'{byte:02X}' for byte in buffer)
                        print("完整数据帧:", hex_data_string)
                        break
                    buffer.clear()  # 清空缓冲区
                    frame_started = False  # 重置帧标记
            # 读取数据帧，原始二进制数据，十六进制格式
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
            # 检查是否有完整数据帧、检查起始桢和结束桢
            if len(buffer) > 4 and buffer[0] == 2 and frame_end == target_end_data:
                print("数据帧校验通过")
                # 检查socketio连接
                if socketio is None:
                    print("socketio not open")
                else:
                    print("socketio open, send read_card_status")
                    socketio.emit('read_card_status', {'data': "enter"})
                # 先查询card_id是否在数据库中
                users, column_names = dbHelper.get_user_by_card_id(card_id)
                if len(users) == 1:  # 成功提示请测试电阻
                    user = users[0]
                    _num = column_names.index('num')
                    _name = column_names.index('name')
                    _department = column_names.index('department')
                    _employee_id = column_names.index('employee_id')
                    _pic_path = column_names.index('pic_path')
                    user_num = user[_num]
                    user_name = user[_name]
                    user_department = user[_department]
                    user_employee_id = user[_employee_id]
                    user_pic_path = user[_pic_path]
                    # 完成测试电阻，是否开门，插入进出记录表的工作
                    print("测试电阻中...")
                    result = get_r()
                    if result is None:
                        # 处理 None 情况
                        service_id, value_hand_left, value_hand_right, value_foot_left, value_foot_right = None, None, None, None, None
                        hand_left_min = Config.HAND_LEFT_MIN
                        hand_left_max = Config.HAND_LEFT_MAX
                        hand_right_min = Config.HAND_RIGHT_MIN
                        hand_right_max = Config.HAND_RIGHT_MAX
                        foot_left_min = Config.FOOT_LEFT_MIN
                        foot_left_max = Config.FOOT_LEFT_MAX
                        foot_right_min = Config.FOOT_RIGHT_MIN
                        foot_right_max = Config.FOOT_RIGHT_MAX
                        result_hand_left = 2
                        result_hand_right = 2
                        result_foot_left = 2
                        result_foot_right = 2
                        result = 2
                    else:
                        service_id, value_hand_left, value_hand_right, value_foot_left, value_foot_right = result
                        print("service_id:", service_id)
                        hand_left_min = Config.HAND_LEFT_MIN
                        hand_left_max = Config.HAND_LEFT_MAX
                        hand_right_min = Config.HAND_RIGHT_MIN
                        hand_right_max = Config.HAND_RIGHT_MAX
                        foot_left_min = Config.FOOT_LEFT_MIN
                        foot_left_max = Config.FOOT_LEFT_MAX
                        foot_right_min = Config.FOOT_RIGHT_MIN
                        foot_right_max = Config.FOOT_RIGHT_MAX
                        if hand_left_min <= value_hand_left <= hand_left_max:
                            result_hand_left = 1
                        else:
                            result_hand_left = 2
                        if hand_right_min <= value_hand_right <= hand_right_max:
                            result_hand_right = 1
                        else:
                            result_hand_right = 2
                        if foot_left_min <= value_foot_left <= foot_left_max:
                            result_foot_left = 1
                        else:
                            result_foot_left = 2
                        if foot_right_min <= value_foot_right <= foot_right_max:
                            result_foot_right = 1
                        else:
                            result_foot_right = 2
                        if result_hand_left == 1 and result_hand_right == 1 and result_foot_left == 1 and result_foot_right == 1:
                            result = 1
                        else:
                            result = 2
                    if socketio is None:
                        print("socketio not open")
                    else:
                        set_data = {
                            'card_id': card_id,
                            'access_flag': 1,
                            'service_id': service_id,
                            'num': user_num,
                            'name': user_name,
                            'employee_id': user_employee_id,
                            'department': user_department,
                            'pic_path': user_pic_path,
                            'value_hand_left': value_hand_left,
                            'value_hand_right': value_hand_right,
                            'value_foot_left': value_foot_left,
                            'value_foot_right': value_foot_right,
                            'result_hand_left': result_hand_left,
                            'result_hand_right': result_hand_right,
                            'result_foot_left': result_foot_left,
                            'result_foot_right': result_foot_right,
                            'hand_left_min': hand_left_min,
                            'hand_left_max': hand_left_max,
                            'hand_right_min': hand_right_min,
                            'hand_right_max': hand_right_max,
                            'foot_left_min': foot_left_min,
                            'foot_left_max': foot_left_max,
                            'foot_right_min': foot_right_min,
                            'foot_right_max': foot_right_max,
                        }
                        print(set_data)
                        socketio.emit('success_data', {'data': set_data})
                    if result == 1:
                        print("开门中...")
                        open_door()
                else:  # 失败表示无权限通过
                    print("无权限通过")
                    error_data = {
                        'card_id': card_id
                    }
                    socketio.emit('fail_data', {'data': error_data})
                # 清除已处理的数据帧
                del buffer[:]
                print("del_buffer", buffer)
    except serial.SerialException as e:
        print(f"串口连接错误: {e}")
    except Exception as e:
        print(f"其他系统错误: {e}")


# 整个读卡出门过程access_flag=2
def leave_card_process(_port, _baudrates, socketio=None):
    try:
        # 打开串行端口
        frame_timeout_ms = Config.default_com_timeout
        with serial.Serial(_port, _baudrates, timeout=frame_timeout_ms / 1000) as ser:
            buffer = bytearray()  # 临时存储数据
            frame_started = False  # 标记数据帧是否已经开始
            start_time = time.time()  # 记录帧开始的时间
            print("出门读卡中...")
            while True:
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
                    if buffer:
                        hex_data_string = ' '.join(f'{byte:02X}' for byte in buffer)
                        print("完整数据帧:", hex_data_string)
                        break
                    buffer.clear()  # 清空缓冲区
                    frame_started = False  # 重置帧标记
            # 读取数据帧，原始二进制数据，十六进制格式
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
            # 检查是否有完整数据帧、检查起始桢和结束桢
            if len(buffer) > 4 and buffer[0] == 2 and frame_end == target_end_data:
                print("数据帧校验通过")
                # 检查socketio连接
                if socketio is None:
                    print("socketio not open")
                else:
                    print("socketio open, send read_card_status")
                    socketio.emit('read_card_status', {'data': "leave"})
                # 先查询card_id是否在数据库中
                users, column_names = dbHelper.get_user_by_card_id(card_id)
                if len(users) == 1:  # 查询成功
                    user = users[0]
                    _num = column_names.index('num')
                    _name = column_names.index('name')
                    _department = column_names.index('department')
                    _employee_id = column_names.index('employee_id')
                    _pic_path = column_names.index('pic_path')
                    user_num = user[_num]
                    user_name = user[_name]
                    user_department = user[_department]
                    user_employee_id = user[_employee_id]
                    user_pic_path = user[_pic_path]
                    set_data = {
                        'card_id': card_id,
                        'access_flag': 2,
                        'num': user_num,
                        'name': user_name,
                        'employee_id': user_employee_id,
                        'department': user_department,
                        'pic_path': user_pic_path,
                    }
                    print(set_data)
                    socketio.emit('success_data', {'data': set_data})
                    print("开门中...")
                    open_door()
                else:  # 失败表示无权限通过
                    print("无权限通过")
                    error_data = {
                        'card_id': card_id
                    }
                    socketio.emit('fail_data', {'data': error_data})
                # 清除已处理的数据帧
                del buffer[:]
                print("del_buffer", buffer)
    except serial.SerialException as e:
        print(f"串口连接错误: {e}")
    except Exception as e:
        print(f"其他系统错误: {e}")


if __name__ == "__main__":
    baudrates = Config.default_baudrates
    port = Config.test_enter_card_port
    if port is None:
        print(f"读卡进门串口{port}未找到，请检查设备连接。")
    else:
        enter_card_process(port, baudrates)
