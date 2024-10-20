import serial
import serial.tools.list_ports
import time

from config import Config


def turn_16_to_10(hex_array):
    decimal_value = 0
    for i, byte in enumerate(reversed(hex_array)):
        decimal_value += byte * (16 ** (i * 2))
    return decimal_value


# 根据名称查找串口
def find_serial_port(_name):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if _name in p.description:
            return p.device
    return None


# 发送数据桢
def set_hex_data(ser, hex_data):
    if isinstance(hex_data, str):
        data = bytearray.fromhex(hex_data)  # 如果是字符串，转换为 bytearray
    else:
        data = hex_data  # 否则直接使用传入的 hex_data
    ser.write(data)
    # print("Sent Data:", ' '.join(f'{byte:02X}' for byte in data))


# 获取返回信息
def get_return_msg(ser, timeout=Config.default_com_timeout):
    start_time = time.time()
    buffer = bytearray()
    while True:
        # 如果有数据可读
        if ser.in_waiting > 0:
            buffer.extend(ser.read(ser.in_waiting))
        # 超过指定时间退出
        if time.time() - start_time > timeout:
            break
        # 检查是否已经收到数据，如果有数据且稳定，则提前退出
        if len(buffer) > 0:
            time.sleep(0.1)  # 稍作等待，以确保数据传输稳定
            if ser.in_waiting == 0:
                break
    printf_byte(buffer)
    return buffer


# 打印获取的信息的十六进制表示
def printf_byte(data):
    # 将数据转换为十六进制字符串
    hex_received_data = ' '.join(f'{byte:02X}' for byte in data)
    # 打印接收的数据
    print(f"Received Data: {hex_received_data}")


# 定义 自定义CRC-8 函数
def crc8(data: bytes, poly=0x31, init=0xFF, refin=True, refout=True, xorout=0x00):
    # Helper functions for bitwise operations
    def reflect(data, width):
        reflection = 0
        for i in range(width):
            if data & (1 << i):
                reflection |= (1 << (width - 1 - i))
        return reflection

    # Initialize variables
    crc = init
    # Reflect input data if required
    if refin:
        data = bytes(reflect(b, 8) for b in data)
    # Process each byte of data
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFF  # Ensure CRC remains 8-bit
    # Reflect output CRC if required
    if refout:
        crc = reflect(crc, 8)
    # Apply final XOR value
    crc ^= xorout
    return crc


# 对数据帧data最后一位的CRC位进行校验
def crc8_check(data):
    le = len(data)
    # 接收的数据帧中的 CRC 值
    received_crc = data[le - 1]
    # 计算CRC
    calculated_crc_hex = crc8(data[:le - 1])
    # 检查接收的 CRC 是否与计算出的一致
    if calculated_crc_hex == received_crc:
        return True
    else:
        print(f"CRC 校验失败！data: {data}, 计算出的 CRC: {calculated_crc_hex}, 接收的 CRC: {received_crc}")
        return False
