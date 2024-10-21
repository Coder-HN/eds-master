import serial
import serial.tools.list_ports
from utils.portHelper import set_hex_data, get_return_msg, printf_byte, crc8_check, turn_16_to_10, \
    crc8
from config import Config

"""
电阻
"""


def standard_r(test_part: int, test_step: int, _port=Config.test_r_port,
               _baudrates=Config.default_baud_rate):  # 1~4  # 1~8
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
