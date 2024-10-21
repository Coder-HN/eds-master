import queue
import time

import serial
import serial.tools.list_ports

from config import Config
from utils import dbHelper
from utils.dbHelper import get_r_standard_by_service_id
from utils.portHelper import get_return_msg, set_hex_data, turn_16_to_10, crc8_check

# 全局队列
enter_queue = queue.Queue()
exit_queue = queue.Queue()
electric_queue = queue.Queue()
manage_queue = queue.Queue()


# 进门读卡监听线程
def monitor_entrance(port, baudrate):
    """监控进门刷卡"""
    try:
        with serial.Serial(port, baudrate, timeout=Config.default_com_timeout) as ser:
            print("进门读卡监听中......")
            while True:
                # 读取数据
                buffer = get_return_msg(ser)
                # 读取到完整数据帧
                if len(buffer) > 4 and buffer[0] == Config.card_start_data and buffer[-3:] == Config.card_end_data:
                    # 获取卡号card_id = buffer[1:-3].decode('ascii')
                    frame_data = buffer[1:-3]  # 将每个十六进制数转换为对应的 ASCII 字符
                    ascii_chars_card = [chr(byte) for byte in frame_data]
                    card_id = ''.join(ascii_chars_card)
                    enter_queue.put(card_id)  # 将卡号放入队列
                    print(f"==================进门刷卡: {list(enter_queue.queue)}")
                time.sleep(0.01)
    except Exception as e:
        print(f"进门串口错误: {e}")
        error_data = {'error_message': f"进门串口错误: {e}"}
        set_data = {'data': error_data}
        manage_queue.put(('fail_data', set_data))


# 出门读卡监听线程
def monitor_exit(port, baudrate):
    """监控出门刷卡"""
    try:
        with serial.Serial(port, baudrate, timeout=Config.default_com_timeout) as ser:
            print("出门读卡监听中......")
            while True:
                # 读取数据
                buffer = get_return_msg(ser)
                # 读取到完整数据帧
                if len(buffer) > 4 and buffer[0] == Config.card_start_data and buffer[-3:] == Config.card_end_data:
                    # 获取卡号card_id = buffer[1:-3].decode('ascii')
                    frame_data = buffer[1:-3]  # 将每个十六进制数转换为对应的 ASCII 字符
                    ascii_chars_card = [chr(byte) for byte in frame_data]
                    card_id = ''.join(ascii_chars_card)
                    exit_queue.put(card_id)  # 将卡号放入队列
                    print(f"==================出门刷卡: {list(exit_queue.queue)}")
                time.sleep(0.01)
    except Exception as e:
        print(f"出门串口错误: {e}")
        error_data = {'error_message': f"出门串口错误: {e}"}
        set_data = {'data': error_data}
        manage_queue.put(('fail_data', set_data))


# 发送信息到前端线程
def manage_system(socketio):
    """管理线程"""
    while True:
        if not enter_queue.empty():
            access_flag = 1
            socketio.emit('read_card_status', {'status': access_flag})
            card_id = enter_queue.queue[0]  # 获取队头元素但不移除
            print(f"处理进门卡号: {card_id}")
            user = dbHelper.get_user_by_card_id(card_id)
            if user is not None:
                # 先跳转
                socketio.emit('read_card_status', {'status': access_flag})
                send_user_info(access_flag, user, card_id, socketio)
                user_info = {'user_num': user['num'], 'card_id': card_id}
                electric_queue.put(('test_resistance', user_info))

            else:
                # TODO 需要把前端video和enter页面放在一起，实现一块监听
                time.sleep(1)  # 等待前端监听
                print(f"card_id={card_id}不在数据库中，无权限通过")
                error_data = {'error_message': f"该卡人员不在数据库中,无权限通过,card_id={card_id}"}
                socketio.emit('fail_data', {'data': error_data})
            enter_queue.get()  # 移除进门读卡

        if not exit_queue.empty():
            access_flag = 2
            socketio.emit('read_card_status', {'status': access_flag})
            card_id = exit_queue.queue[0]  # 获取队头元素但不移除

            print(f"处理出门卡号: {card_id}")
            user = dbHelper.get_user_by_card_id(card_id)
            if user is not None:
                socketio.emit('read_card_status', {'status': access_flag})
                send_user_info(access_flag, user, card_id, socketio)
                electric_queue.put(('open_door', card_id))
            else:
                time.sleep(1)  # 等待前端监听
                print(f"card_id={card_id}不在数据库中，无权限通过")
                error_data = {'error_message': f"该卡人员不在数据库中,无权限通过,card_id={card_id}"}
                socketio.emit('fail_data', {'data': error_data})
            exit_queue.get()

        if not manage_queue.empty():
            res, set_data = manage_queue.get()
            if res == 'success_data':
                socketio.emit('success_data', set_data)
            elif res == 'fail_data':
                socketio.emit('fail_data', set_data)
        time.sleep(0.1)


# 电阻串口线程
def electric_control(port, baudrate):
    """电阻线程，处理开门和电阻测试事务"""
    try:
        with (serial.Serial(port, baudrate, timeout=Config.default_com_timeout) as ser):
            while True:
                if not electric_queue.empty():
                    task, user_info = electric_queue.get()
                    if task == 'test_resistance':
                        print(f"电阻测试中: user_info={user_info}")
                        resistance_value = get_resistance(ser)
                        r_standard = get_r_standard_by_service_id(resistance_value['service_id'])
                        results = compare_resistance_values(resistance_value, r_standard)
                        if results['result_num'] == 1:
                            print(f"电阻测试成功: user_info={user_info}")
                            set_data = {
                                'data': get_send_resistance_info(user_info, resistance_value, r_standard, results)}
                            manage_queue.put(('success_data', set_data))
                            open_door(ser)  # 一次测试成功开门
                        else:
                            print(f"电阻测试失败，重新测试: user_info={user_info}")
                            repeat_test_resistance(ser, user_info, r_standard)

                    elif task == 'open_door':
                        print(f"开门操作中: user_info={user_info}")
                        open_door(ser)
                time.sleep(0.1)
    except Exception as e:
        print(f"电阻串口错误: {e}")
        error_data = {'error_message': f"电阻串口错误: {e}"}
        set_data = {'data': error_data}
        manage_queue.put(('fail_data', set_data))


def send_user_info(access_flag, user, card_id, socketio):
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


def get_send_resistance_info(user_info, resistance_value, r_standard, results):
    return {
        'access_flag': 1,
        'user_num': user_info['user_num'],
        'card_id': user_info['card_id'],
        'service_id': resistance_value['service_id'],

        'hand_left_min': r_standard['hand_left_min'],
        'hand_left_max': r_standard['hand_left_max'],
        'hand_right_min': r_standard['hand_right_min'],
        'hand_right_max': r_standard['hand_right_max'],
        'foot_left_min': r_standard['foot_left_min'],
        'foot_left_max': r_standard['foot_left_max'],
        'foot_right_min': r_standard['foot_right_min'],
        'foot_right_max': r_standard['foot_right_max'],

        'value_hand_left': resistance_value['value_hand_left'],
        'value_hand_right': resistance_value['value_hand_right'],
        'value_foot_left': resistance_value['value_foot_left'],
        'value_foot_right': resistance_value['value_foot_right'],
        'result_hand_left': results['result_hand_left'],
        'result_hand_right': results['result_hand_right'],
        'result_foot_left': results['result_foot_left'],
        'result_foot_right': results['result_foot_right'],

        'result_num': results['result_num'],
    }


def compare_resistance_values(resistance_value, r_standard):
    results = {
        'result_hand_left': 2,  # 默认值为 2，表示超出范围
        'result_hand_right': 2,
        'result_foot_left': 2,
        'result_foot_right': 2
    }
    # 对比手和脚的测试值与限制值
    if r_standard['hand_left_min'] <= resistance_value['value_hand_left'] <= r_standard['hand_left_max']:
        results['result_hand_left'] = 1
    if r_standard['hand_right_min'] <= resistance_value['value_hand_right'] <= r_standard['hand_right_max']:
        results['result_hand_right'] = 1
    if r_standard['foot_left_min'] <= resistance_value['value_foot_left'] <= r_standard['foot_left_max']:
        results['result_foot_left'] = 1
    if r_standard['foot_right_min'] <= resistance_value['value_foot_right'] <= r_standard['foot_right_max']:
        results['result_foot_right'] = 1

    # 计算综合结果 result_num，所有值都为 1 时为通过
    results['result_num'] = 1 if all(value == 1 for value in results.values()) else 0
    return results


def repeat_test_resistance(ser, user_info, r_standard):
    """6秒反复测试电阻，每0.5秒测试一次"""
    for i in range(12, 0, -1):  # 6秒，每0.5秒一次
        resistance_value = get_resistance(ser)
        results = compare_resistance_values(resistance_value, r_standard)
        if results['result_num'] == 1:
            print(f"电阻重新测试成功: user_info={user_info}")
            set_data = {'data': get_send_resistance_info(user_info, resistance_value, r_standard, results)}
            manage_queue.put(('success_data', set_data))
            open_door(ser)  # 一次测试成功开门
            return
        else:  # TODO 可以来检查是否被中断
            time.sleep(0.5)
            queue_length = enter_queue.qsize()
            if queue_length > 1:
                # 重新测试过程中有人重复刷卡
                data = get_send_resistance_info(user_info, resistance_value, r_standard, results)
                data['repeat'] = 1
                set_data = {'data': data}
                manage_queue.put(('success_data', set_data))
            if i != 1:
                # 重新测试过程中未通过需要在每秒刷新页面
                if i % 2 == 0:
                    data = get_send_resistance_info(user_info, resistance_value, r_standard, results)
                    data['second'] = i / 2
                    set_data = {'data': data}
                    manage_queue.put(('success_data', set_data))
            else:
                # 最后一次未通过
                set_data = {'data': get_send_resistance_info(user_info, resistance_value, r_standard, results)}
                manage_queue.put(('success_data', set_data))  # 最终测试失败


def get_resistance(ser):
    # 获取电阻
    set_hex_data(ser, Config.hex_get_cow)
    received_data = get_return_msg(ser)
    service_id = turn_16_to_10(received_data[0:1])
    if crc8_check(received_data):
        cow_data = received_data[3:-2]
        left_hand = turn_16_to_10(cow_data[:4]) / 1000
        right_hand = turn_16_to_10(cow_data[4:8]) / 1000
        left_foot = turn_16_to_10(cow_data[8:12]) / 1000
        right_foot = turn_16_to_10(cow_data[12:16]) / 1000
        return {
            'service_id': service_id,
            'value_hand_left': left_hand,
            'value_hand_right': right_hand,
            'value_foot_left': left_foot,
            'value_foot_right': right_foot
        }


def open_door(ser):
    # 开门
    set_hex_data(ser, Config.hex_open_door)
    received_data = get_return_msg(ser)
    if crc8_check(received_data) and bytearray.fromhex(Config.hex_open_door_success) == received_data:
        print("获取开门请求成功")
        return True
    else:
        return False
