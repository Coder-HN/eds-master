import serial
import serial.tools.list_ports
from utils.portHelper import set_hex_data, get_return_msg, printf_byte, crc8_check, turn_16_to_10, \
    crc8
from config import Config

"""
测试电阻
"""


def _open_door(_port, _baudrates):
    try:
        # 打开串行端口
        with serial.Serial(_port, _baudrates, timeout=1) as ser:
            # 开门
            set_hex_data(ser, Config.hex_open_door)
            received_data = get_return_msg(ser)
            if crc8_check(received_data) and bytearray.fromhex(Config.hex_open_door_success) == received_data:
                print("获取开门请求成功")
                return True
            else:
                return False
    except serial.SerialException as e:
        print(f"串口错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")


def open_door():
    baudrates = Config.default_baud_rate
    port = Config.test_r_port
    if port is None:
        print(f"测试电阻串口{port}未找到，请检查设备连接。")
        return None
    else:
        # 开门
        return _open_door(port, baudrates)


def _get_r(_port, _baudrates):
    try:
        # 打开串行端口
        with serial.Serial(_port, _baudrates, timeout=1) as ser:
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
                # print(f"service_id:{service_id}, left_hand:{left_hand}, right_hand:{right_hand}, left_foot:{left_foot}, right_foot:{right_foot}")
                return service_id, left_hand, right_hand, left_foot, right_foot
    except serial.SerialException as e:
        print(f"串口错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")


def get_r():
    baudrates = Config.default_baud_rate
    port = Config.test_r_port
    if port is None:
        print(f"测试电阻串口{port}未找到，请检查设备连接。")
        return None
    else:
        # 获取电阻
        return _get_r(port, baudrates)


def _standard_r(_port, _baudrates, test_part: int, test_step: int):  # 1~4  # 1~8
    try:
        # 打开串行端口
        with serial.Serial(_port, _baudrates, timeout=1) as ser:
            # 校准格式
            # 发01 05 01(part) 00 00 00 01(step) 01 CRC
            # 收01 05 01(part) 00 00 00 01(step) 05 CRC
            _hex_r_standard_send = f"01 05 0{str(test_part)} 00 00 00 0{str(test_step)} 01"
            _hex_r_standard_get = f"01 05 0{str(test_part)} 00 00 00 0{str(test_step)} 05"
            hex_r_standard_send = _hex_r_standard_send + f" {crc8(bytearray.fromhex(_hex_r_standard_send)):02X}"
            hex_r_standard_get = _hex_r_standard_get + f" {crc8(bytearray.fromhex(_hex_r_standard_get)):02X}"
            print(hex_r_standard_send)
            print(hex_r_standard_get)
            set_hex_data(ser, hex_r_standard_send)
            received_data = get_return_msg(ser)
            if received_data == hex_r_standard_get:
                print(f"test_part={test_part},test_step={test_step},电阻校准成功")
                return True
            else:
                return False
    except serial.SerialException as e:
        print(f"串口错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")


def standard_r(test_part: int, test_step: int):
    baudrates = Config.default_baud_rate
    port = Config.test_r_port
    if port is None:
        print(f"测试电阻串口{port}未找到，请检查设备连接。")
        return None
    else:
        # 开门
        return _standard_r(port, baudrates, test_part, test_step)
