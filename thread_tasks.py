import queue
import time
from datetime import datetime

import serial
import serial.tools.list_ports

from config import Config
from utils import dbHelper
from utils.dbHelper import get_test_standard_by_service_id
from utils.portHelper import get_return_msg
from utils.testResistanceHelper import get_resistance, open_door, standard_r


# 刷卡信息
def generate_swipe_data(access_flag):
    swipe_data = {
        'access_flag': access_flag
    }
    return swipe_data


# 错误信息
def generate_fail_data(access_flag, message_type, error_message, card_id=None):
    fail_data = {
        'access_flag': access_flag,  # 进出门 1/2,
        'card_id': card_id,  # 权限错误时使用
        'message_type': message_type,  # 1无权限错误/2设备错误,
        'error_message': error_message  # 错误信息
    }
    return fail_data


# 用户信息
def generate_user_data(access_flag, card_id, service_id, user_num, name, employee_id, department, pic_path):
    user_data = {
        'access_flag': access_flag,
        'card_id': card_id,

        'service_id': service_id,

        'user_num': user_num,
        'name': name,
        'employee_id': employee_id,
        'department': department,
        'pic_path': pic_path,
    }
    return user_data


# 测试电阻信息,repeat表示在重复测试时是否有重复刷卡
def generate_r_data(user_info, resistance_value, r_standard, results, second=float(-1), repeat=-1):
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

        'repeat': repeat,
        'second': second,
    }


"""
user_info = {'access_flag': access_flag, 'user_num': user['num'], 'card_id': card_id}
"""

# 全局队列
enter_queue = queue.Queue()
exit_queue = queue.Queue()
electric_queue = queue.Queue()
manage_queue = queue.Queue()
standard_r_queue = queue.Queue()
is_repeat_test = False  # 是否正在重新测试电阻


# 进门读卡监听线程
def monitor_entrance(port, baudrate):
    try:
        with serial.Serial(port, baudrate, timeout=Config.default_com_timeout) as ser:
            print("进门读卡监听中......")
            is_standard_r = standard_r_queue.qsize()
            if is_standard_r != 0:
                print("正在进行电阻校验，刷卡无效！")
            while True:
                if is_standard_r == 0:
                    # 读取数据
                    buffer = get_return_msg(ser)
                    # 读取到完整数据帧
                    if len(buffer) > 4 and buffer[0] == Config.card_start_data and buffer[-3:] == Config.card_end_data:
                        # 获取卡号
                        card_id = buffer[1:-3].decode('ascii')
                        enter_queue.put(card_id)  # 将卡号放入队列
                        print(f"==================进门刷卡: {list(enter_queue.queue)}")
                    buffer.clear()
                time.sleep(0.01)
    except Exception as e:
        print(f"进门串口错误: {e}")
        fail_data = generate_fail_data(1, 2, f"进门串口错误: {e}")
        manage_queue.put(('fail_data', fail_data))


# 出门读卡监听线程
def monitor_exit(port, baudrate):
    try:
        with serial.Serial(port, baudrate, timeout=Config.default_com_timeout) as ser:
            print("出门读卡监听中......")
            is_standard_r = standard_r_queue.qsize()
            if is_standard_r != 0:
                print("正在进行电阻校验，刷卡无效！")
            while True:
                if is_standard_r == 0:
                    # 读取数据
                    buffer = get_return_msg(ser)
                    # 读取到完整数据帧
                    if len(buffer) > 4 and buffer[0] == Config.card_start_data and buffer[-3:] == Config.card_end_data:
                        print("出门读卡-当前时间（时:分:秒.毫秒）：", datetime.now().strftime("%H:%M:%S.%f")[:-3])
                        # 获取卡号
                        card_id = buffer[1:-3].decode('ascii')
                        exit_queue.put(card_id)  # 将卡号放入队列
                        print(f"==================出门刷卡: {list(exit_queue.queue)}")
                    buffer.clear()
                time.sleep(0.01)
    except Exception as e:
        print(f"出门串口错误: {e}")
        fail_data = generate_fail_data(2, 2, f"进门串口错误: {e}")
        manage_queue.put(('fail_data', fail_data))


# 发送信息到前端线程
def manage_system(socketio):
    while True:
        if not enter_queue.empty():
            global is_repeat_test
            if is_repeat_test:  # 如果在正在重新测试时收到刷卡，停止重新测试
                is_repeat_test = False
            # 先跳转
            access_flag = 1
            swipe_data = generate_swipe_data(access_flag)
            socketio.emit('swipe_data', swipe_data)
            card_id = enter_queue.queue[0]  # 获取队头元素但不移除
            user = dbHelper.get_user_by_card_id(card_id)
            if user is not None:
                send_user_data(access_flag, user, card_id, socketio)
                user_info = {'access_flag': access_flag, 'user_num': user['num'], 'card_id': card_id}
                electric_queue.put(('test_resistance', user_info))
                print("已放置electric_queue")

            else:
                fail_data = generate_fail_data(access_flag, 1, None, card_id)
                socketio.emit('fail_data', fail_data)
                print(f"card_id={card_id}不在数据库中，无权限通过，发送fail_data={fail_data}")
            enter_queue.get()  # 移除进门读卡

        if not exit_queue.empty():
            access_flag = 2
            print("出门发送跳转指令-当前时间（时:分:秒.毫秒）：", datetime.now().strftime("%H:%M:%S.%f")[:-3])
            swipe_data = generate_swipe_data(access_flag)
            socketio.emit('swipe_data', swipe_data)
            card_id = exit_queue.queue[0]  # 获取队头元素但不移除
            user = dbHelper.get_user_by_card_id(card_id)
            if user is not None:
                user_info = {"access_flag": access_flag, 'user_num': user['num'], "card_id": card_id}
                print("出门发送开门指令给电阻线程-当前时间（时:分:秒.毫秒）：",
                      datetime.now().strftime("%H:%M:%S.%f")[:-3])
                electric_queue.put(('open_door', user_info))
                send_user_data(access_flag, user, card_id, socketio)
            else:
                fail_data = generate_fail_data(access_flag, 1, None, card_id)
                socketio.emit('fail_data', fail_data)
                print(f"card_id={card_id}不在数据库中，无权限通过，发送fail_data={fail_data}")
            exit_queue.get()

        if not manage_queue.empty():
            res, get_data = manage_queue.get()
            if res == 'r_data':
                access_flag = get_data.get('access_flag')
                msg = "重新测试电阻更新数据"
                if get_data.get('second') == 0:
                    msg = "重新测试电阻正常结束,增加进出记录"
                elif get_data.get('repeat') == 1:
                    msg = "重复刷卡导致重新测试电阻提前结束,增加进出记录"
                elif get_data.get('result_num') == 1:
                    msg = "测试通过,添加进出记录"
                print(f"发送r_data数据到前端,access_flag={access_flag},msg={msg}")
                socketio.emit('r_data', get_data)
            elif res == 'fail_data':
                print(f"发送fail_data数据到前端,fail_data={get_data}")
                socketio.emit('fail_data', get_data)
        time.sleep(0.001)


# 电阻串口线程
def electric_control(port, baudrate):
    try:
        with (serial.Serial(port, baudrate, timeout=Config.default_com_timeout) as ser):
            while True:
                if not electric_queue.empty():
                    task, user_info = electric_queue.get()
                    if task == 'test_resistance':
                        resistance_value = get_resistance(ser)
                        test_standard = get_test_standard_by_service_id(resistance_value['service_id'])
                        results, resistance_value = compare_resistance_values(resistance_value, test_standard)
                        if results['result_num'] == 1:
                            print(f"电阻测试成功: user_info={user_info}")
                            r_data = generate_r_data(user_info, resistance_value, test_standard, results)
                            manage_queue.put(('r_data', r_data))
                            open_door(ser, access_flag=1)  # 一次测试成功开门
                        else:
                            print(f"电阻测试失败，重新测试: user_info={user_info}")
                            repeat_test_resistance(ser, user_info, test_standard)

                    elif task == 'open_door':  # 出门那边发来的请求打开出门的门
                        print(f"开门操作中: user_info={user_info}")
                        print("出门-发送开门指令给设备-当前时间（时:分:秒.毫秒）：",
                              datetime.now().strftime("%H:%M:%S.%f")[:-3])
                        open_door(ser, access_flag=2)

                if not standard_r_queue.empty():
                    test_data = standard_r_queue.get()
                    standard_r(test_data['test_part'], test_data['test_step'], ser)

                time.sleep(0.001)
    except Exception as e:
        print(f"电阻串口错误: {e}")
        fail_data = generate_fail_data(1, 2, f"电阻串口错误: {e}")
        manage_queue.put(('fail_data', fail_data))


def send_user_data(access_flag, user, card_id, socketio):
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
    user_data = generate_user_data(
        access_flag=access_flag,
        card_id=card_id,
        # TODO 出门无法获取service_id
        service_id=None,
        user_num=user_num,
        name=user_name,
        employee_id=user_employee_id,
        department=user_department,
        pic_path=user_pic_path)
    print(f"发送user_data数据到前端,user_data={user_data}")
    socketio.emit('user_data', user_data)


def compare_resistance_values(resistance_value, test_standard):
    results = {
        'result_hand_left': 0,  # 默认值为 0，表示不进行测试
        'result_hand_right': 0,
        'result_foot_left': 0,
        'result_foot_right': 0
    }
    test_part = test_standard['test_part']
    if test_part[0] == '1':
        results['result_hand_left'] = 2
        if test_standard['hand_left_min'] <= resistance_value['value_hand_left'] <= test_standard['hand_left_max']:
            results['result_hand_left'] = 1
    else:
        resistance_value['value_hand_left'] = -1

    if test_part[1] == '1':
        results['result_hand_right'] = 2
        if test_standard['hand_right_min'] <= resistance_value['value_hand_right'] <= test_standard['hand_right_max']:
            results['result_hand_right'] = 1
    else:
        resistance_value['result_hand_right'] = -1

    if test_part[2] == '1':
        results['result_foot_left'] = 2
        results['result_foot_right'] = 2
        if test_standard['foot_left_min'] <= resistance_value['value_foot_left'] <= test_standard['foot_left_max']:
            results['result_foot_left'] = 1
        if test_standard['foot_right_min'] <= resistance_value['value_foot_right'] <= test_standard['foot_right_max']:
            results['result_foot_right'] = 1
    else:
        resistance_value['value_foot_left'] = -1
        resistance_value['value_foot_right'] = -1

    # 计算综合结果 result_num，所有值都为 1 时为通过
    results['result_num'] = 1 if all((value == 1 or value == 0) for value in results.values()) else 0
    return results, resistance_value


# 6秒反复测试电阻，每0.25秒测试一次，每0.5秒一次发送一次数据
def repeat_test_resistance(ser, user_info, test_standard):
    global is_repeat_test
    is_repeat_test = True  # 设置正在重新测试
    for i in range(24, 0, -1):
        resistance_value = get_resistance(ser)
        results, resistance_value = compare_resistance_values(resistance_value, test_standard)
        if results['result_num'] == 1:
            print(f"电阻重新测试成功: user_info={user_info}")
            r_data = generate_r_data(user_info, resistance_value, test_standard, results)
            manage_queue.put(('r_data', r_data))
            open_door(ser, access_flag=1)  # 一次测试成功开门
            return
        else:
            print(f"重新测试：is_repeat_test={is_repeat_test},i={i}")
            if is_repeat_test is not True:
                # 重新测试过程中有人重复刷卡
                r_data = generate_r_data(user_info, resistance_value, test_standard, results, repeat=1)
                manage_queue.put(('r_data', r_data))
                print(f"==================提前结束本次刷卡: user_info={user_info}")
                return
            if i != 1:
                # 重新测试过程中未通过需要在每秒刷新页面
                if i % 4 == 0:
                    r_data = generate_r_data(user_info, resistance_value, test_standard, results, second=i / 4)
                    manage_queue.put(('r_data', r_data))
            else:
                # 最后一次未通过
                r_data = generate_r_data(user_info, resistance_value, test_standard, results, second=0)
                manage_queue.put(('r_data', r_data))
                return
            time.sleep(0.25)


def add_task_standard_r(test_part, test_step):
    test_data = {
        'test_part': test_part,
        'test_step': test_step
    }
    standard_r_queue.put(test_data)
    return True
