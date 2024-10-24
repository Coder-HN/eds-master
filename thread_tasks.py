import queue
import time

import serial
import serial.tools.list_ports

from config import Config
from utils import dbHelper
from utils.dbHelper import get_test_standard_by_service_id
from utils.portHelper import get_return_msg
from utils.testResistanceHelper import get_resistance, open_door, standard_r

# 全局队列
enter_queue = queue.Queue()
exit_queue = queue.Queue()
electric_queue = queue.Queue()
manage_queue = queue.Queue()
standard_r_queue = queue.Queue()


# 进门读卡监听线程
def monitor_entrance(port, baudrate):
    """监控进门刷卡"""
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
                        # 获取卡号card_id = buffer[1:-3].decode('ascii')
                        frame_data = buffer[1:-3]  # 将每个十六进制数转换为对应的 ASCII 字符
                        ascii_chars_card = [chr(byte) for byte in frame_data]
                        card_id = ''.join(ascii_chars_card)
                        enter_queue.put(card_id)  # 将卡号放入队列
                        print(f"==================进门刷卡: {list(enter_queue.queue)}")
                time.sleep(0.01)
    except Exception as e:
        print(f"进门串口错误: {e}")
        error_data = {'message_type': 2, 'error_message': f"进门串口错误: {e}", 'access_flag': 1}
        manage_queue.put(('fail_data', {'data': error_data}))


# 出门读卡监听线程
def monitor_exit(port, baudrate):
    """监控出门刷卡"""
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
                        # 获取卡号card_id = buffer[1:-3].decode('ascii')
                        frame_data = buffer[1:-3]  # 将每个十六进制数转换为对应的 ASCII 字符
                        ascii_chars_card = [chr(byte) for byte in frame_data]
                        card_id = ''.join(ascii_chars_card)
                        exit_queue.put(card_id)  # 将卡号放入队列
                        print(f"==================出门刷卡: {list(exit_queue.queue)}")
                time.sleep(0.01)
    except Exception as e:
        print(f"出门串口错误: {e}")
        error_data = {'message_type': 2, 'error_message': f"出门串口错误: {e}", 'access_flag': 2}
        manage_queue.put(('fail_data', {'data': error_data}))


# 发送信息到前端线程
def manage_system(socketio):
    """管理线程"""
    while True:
        if not enter_queue.empty():
            access_flag = 1
            # 先跳转
            socketio.emit('read_card_status', {'status': access_flag})
            card_id = enter_queue.queue[0]  # 获取队头元素但不移除
            print(f"处理进门卡号: {card_id}")
            user = dbHelper.get_user_by_card_id(card_id)
            if user is not None:
                send_user_info(access_flag, user, card_id, socketio)
                user_info = {'user_num': user['num'], 'card_id': card_id}
                electric_queue.put(('test_resistance', user_info))

            else:
                time.sleep(1)  # 等待前端监听
                print(f"card_id={card_id}不在数据库中，无权限通过")
                error_data = {
                    'message_type': 1,
                    'error_message': f"该卡人员不在数据库中,无权限通过,card_id={card_id}",
                    'access_flag': access_flag
                }
                socketio.emit('fail_data', {'data': error_data})
            enter_queue.get()  # 移除进门读卡

        if not exit_queue.empty():
            access_flag = 2
            socketio.emit('read_card_status', {'status': access_flag})
            card_id = exit_queue.queue[0]  # 获取队头元素但不移除

            print(f"处理出门卡号: {card_id}")
            user = dbHelper.get_user_by_card_id(card_id)
            if user is not None:
                send_user_info(access_flag, user, card_id, socketio)
                user_info = {"card_id": card_id, "access_flag": access_flag}
                electric_queue.put(('open_door', user_info))
            else:
                time.sleep(1)  # 等待前端监听
                print(f"card_id={card_id}不在数据库中，无权限通过")
                error_data = {
                    'message_type': 1,
                    'error_message': f"该卡人员不在数据库中,无权限通过,card_id={card_id}",
                    'access_flag': access_flag
                }
                socketio.emit('fail_data', {'data': error_data})
            exit_queue.get()

        if not manage_queue.empty():
            res, set_data = manage_queue.get()
            if res == 'success_data':
                access_flag = 1
                if set_data['data'].get('access_flag') is not None:
                    access_flag = set_data['data'].get('access_flag')
                msg = "重新测试电阻更新数据"
                if set_data['data'].get('second') == 0:
                    msg = "重新测试电阻正常结束,增加进出记录"
                elif set_data['data'].get('repeat') == 1:
                    msg = "重复刷卡导致重新测试电阻提前结束,增加进出记录"
                elif set_data['data'].get('result_num') == 1:
                    msg = "测试通过,添加进出记录"
                print(f"发送success_data数据到前端,access_flag={access_flag},msg={msg}")
                socketio.emit('success_data', set_data)
            elif res == 'fail_data':
                print(f"发送fail_data数据到前端,fail_data={set_data}")
                socketio.emit('fail_data', set_data)
        time.sleep(0.01)


# 电阻串口线程
def electric_control(port, baudrate):
    """电阻线程，处理开门和电阻测试事务"""
    try:
        with (serial.Serial(port, baudrate, timeout=Config.default_com_timeout) as ser):
            while True:
                if not electric_queue.empty():
                    task, user_info = electric_queue.get()
                    if task == 'test_resistance':
                        print("电阻测试中...")
                        resistance_value = get_resistance(ser)
                        test_standard = get_test_standard_by_service_id(resistance_value['service_id'])
                        results, resistance_value = compare_resistance_values(resistance_value, test_standard)
                        if results['result_num'] == 1:
                            print(f"电阻测试成功: user_info={user_info}")
                            set_data = {
                                'data': get_send_resistance_info(user_info, resistance_value, test_standard, results)}
                            manage_queue.put(('success_data', set_data))
                            open_door(ser, access_flag=1)  # 一次测试成功开门
                        else:
                            print(f"电阻测试失败，重新测试: user_info={user_info}")
                            repeat_test_resistance(ser, user_info, test_standard)

                    elif task == 'open_door':  # 出门那边发来的请求打开出门的门
                        print(f"开门操作中: user_info={user_info}")
                        open_door(ser, access_flag=2)
                if not standard_r_queue.empty():
                    test_data = standard_r_queue.get()
                    standard_r(test_data['test_part'], test_data['test_step'], ser)

                time.sleep(0.01)
    except Exception as e:
        print(f"电阻串口错误: {e}")
        error_data = {'message_type': 2, 'error_message': f"电阻串口错误: {e}", 'access_flag': 1}
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
        print(f"发送cache_data数据到前端,cache_data={cache_data}")
        socketio.emit('cache_data', {'data': cache_data})
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
        print("发送success_data数据到前端")
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


def repeat_test_resistance(ser, user_info, test_standard):
    """6秒反复测试电阻，每0.25秒测试一次，每0.5秒一次发送一次数据"""
    for i in range(24, 0, -1):
        resistance_value = get_resistance(ser)
        results, resistance_value = compare_resistance_values(resistance_value, test_standard)
        if results['result_num'] == 1:
            print(f"电阻重新测试成功: user_info={user_info}")
            set_data = {'data': get_send_resistance_info(user_info, resistance_value, test_standard, results)}
            manage_queue.put(('success_data', set_data))
            open_door(ser, access_flag=1)  # 一次测试成功开门
            return
        else:
            queue_length = enter_queue.qsize()
            print(f"重新测试：queue_length={queue_length},i={i}")
            if queue_length >= 1:
                # 重新测试过程中有人重复刷卡
                data = get_send_resistance_info(user_info, resistance_value, test_standard, results)
                data['repeat'] = 1
                set_data = {'data': data}
                manage_queue.put(('success_data', set_data))
                print(f"==================提前结束本次刷卡: user_info={user_info}")
                return
            if i != 1:
                # 重新测试过程中未通过需要在每秒刷新页面
                if i % 2 == 0:
                    data = get_send_resistance_info(user_info, resistance_value, test_standard, results)
                    data['second'] = i / 4
                    set_data = {'data': data}
                    manage_queue.put(('success_data', set_data))
            else:
                # 最后一次未通过
                data = get_send_resistance_info(user_info, resistance_value, test_standard, results)
                data['second'] = 0
                set_data = {'data': data}
                manage_queue.put(('success_data', set_data))  # 最终测试失败
                return
            time.sleep(0.25)


def add_task_standard_r(test_part, test_step):
    test_data = {
        'test_part': test_part,
        'test_step': test_step
    }
    standard_r_queue.put(test_data)
    return True
