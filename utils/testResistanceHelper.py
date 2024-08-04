import serial
import serial.tools.list_ports
from utils.portHelper import find_serial_port, set_hex_data, get_return_msg, printf_byte, crc8_check, turn_16_to_10
from config import Config

"""
测试电阻
"""


def _open_door(_port, _baudrates):
    # 打开串行端口
    with serial.Serial(_port, _baudrates, timeout=1) as ser:
        # 开门
        set_hex_data(ser, Config.hex_open_door)
        received_data = get_return_msg(ser)
        printf_byte(received_data)
        if crc8_check(received_data) and bytearray.fromhex(Config.hex_open_door_success) == received_data:
            print("获取开门请求成功")
            return True
        else:
            return False


def open_door():
    baudrates = Config.default_baudrates
    name = Config.test_r_name
    port = find_serial_port(name)
    if port is None:
        print(f"测试器{name}串口未找到，请检查设备连接。")
        return None
    else:
        # 开门
        return _open_door(port, baudrates)


def _get_r(_port, _baudrates):
    # 打开串行端口
    with serial.Serial(_port, _baudrates, timeout=1) as ser:
        set_hex_data(ser, Config.hex_test_online)
        received_data = get_return_msg(ser)
        printf_byte(received_data)
        # CRC校验
        if crc8_check(received_data) and bytearray.fromhex(Config.hex_test_online_succcess) == received_data:
            print("获取在线状态成功")
            service_id = turn_16_to_10(received_data[0:1])
            # 获取电阻
            set_hex_data(ser, Config.hex_get_cow)
            received_data = get_return_msg(ser)
            printf_byte(received_data)
            if crc8_check(received_data):
                print("获取电阻成功")
                cow_data = received_data[3:-2]
                left_hand = turn_16_to_10(cow_data[:4]) / 1000
                right_hand = turn_16_to_10(cow_data[4:8]) / 1000
                left_foot = turn_16_to_10(cow_data[8:12]) / 1000
                right_foot = turn_16_to_10(cow_data[12:16]) / 1000
                print(f"left_hand:{left_hand}, right_hand:{right_hand}, left_foot:{left_foot}, right_foot:{right_foot}")
                return service_id, left_hand, right_hand, left_foot, right_foot


def get_r():
    baudrates = Config.default_baudrates
    name = Config.test_r_name
    port = find_serial_port(name)
    if port is None:
        print(f"测试器{name}串口未找到，请检查设备连接。")
        return None
    else:
        # 获取电阻
        return _get_r(port, baudrates)
