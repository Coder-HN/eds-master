import serial
import serial.tools.list_ports
from config import Config
from utils import dbHelper
from utils.portHelper import find_serial_port, turn_16_to_10
from utils.testResistanceHelper import get_r, open_door

"""
读卡器
假设接收的数据帧为 02 09 01 E0 0F E2 77 72 03：
1. 帧起始（02）：标识帧的起始。
2. 长度字段（09）：表示数据帧的总长度，包括起始和校验和在内。
3. 命令代码（01）：表示具体的命令类型，如REQA、SELECT等。
4. 数据字段（E0 0F E2 77 72）：具体的命令数据或响应数据。
5. 校验和（03）：用于验证数据的完整性。
"""


# 读卡器校验位校验方法 #TODO 有问题
def calculate_checksum(frame):
    print(f"frame: {' '.join(f'{byte:02X}' for byte in frame)}")
    # 计算校验和
    checksum = 0
    for byte in frame[:-1]:  # 除了最后一个字节（校验和本身），总和为710
        checksum += byte
    calculated_checksum = checksum % 256
    # 验证校验和
    received_checksum = frame[-1]
    print("数据帧校验和:", received_checksum)
    print("计算的校验和:", calculated_checksum)
    if calculated_checksum == received_checksum:
        print("校验通过")
        return True
    else:
        print("校验失败")
        return False


# 整个读卡进门，测试电阻过程
def enter_card_data(_port, _baudrates, socketio=None):
    try:
        # 打开串行端口
        with serial.Serial(_port, _baudrates, timeout=1) as ser:
            buffer = bytearray()  # 一个字节可以存02
            while True:
                # 读取所有可用的数据
                data = ser.read(ser.in_waiting)
                if data:
                    # 将数据添加到缓冲区
                    buffer.extend(data)
                    # 检查是否有完整数据帧、检查校验和是否正确
                    if len(buffer) >= 2 and buffer[0] == 2 and len(buffer) == buffer[1]:
                        print("读卡中--------------------------------------------------")
                        # 数据帧校验
                        calculate_checksum(buffer)
                        # 处理数据帧
                        frame_data = buffer[3:-2]
                        card_id = turn_16_to_10(frame_data)
                        print("card_id:", card_id)
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
                            print("测试电阻中--------------------------------------------------")
                            result = get_r()
                            if result is None:
                                # 处理 None 情况
                                service_id, value_hand_left, value_hand_right, value_foot_left, value_foot_right = None, None, None, None, None
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
                                socketio.emit('serial_data', {'data': set_data})
                            if result == 1:
                                print("开门中--------------------------------------------------")
                                open_door()
                        else:  # 失败表示无权限通过
                            print("无权限通过")
                        # 清除已处理的数据帧
                        del buffer[:]
                        print("del_buffer", buffer)
    except serial.SerialException as e:
        print(f"串口错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")


# 整个读卡进门，测试电阻过程
def outdoor_card_data(_port, _baudrates, socketio=None):
    pass;


if __name__ == "__main__":
    baudrates = Config.default_baudrates
    # name = Config.test_enter_card_name
    # port = find_serial_port(name)
    port = Config.test_enter_card_port
    if port is None:
        print(f"读卡进门串口{port}未找到，请检查设备连接。")
    else:
        enter_card_data(port, baudrates)
