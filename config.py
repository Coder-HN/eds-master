class Config:
    HOST = 'localhost'
    USER = 'root'
    PASSWORD = 'root'
    DATABASE = 'edsystem'
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQL_DATA = 'E:/workplaces/PythonProjects/edsMaster/static_data'
    # 静态文件位置
    STATIC_PUBLIC = 'E:/workplaces/FrontProjects/edsFront/public'
    # 头像位置
    UPLOAD_FOLDER = 'E:/workplaces/FrontProjects/edsFront/public/profile_photo/'
    # 静电测试电阻上下限配置，以K为单位
    HAND_LEFT_MIN = 100
    HAND_LEFT_MAX = 15000  # 15M
    HAND_RIGHT_MIN = 100
    HAND_RIGHT_MAX = 15000
    FOOT_LEFT_MIN = 100
    FOOT_LEFT_MAX = 60000  # 60M
    FOOT_RIGHT_MIN = 100
    FOOT_RIGHT_MAX = 60000
    # 串口名称
    SERIAL_PORT_NAME = ''
    # 在岗时间要求、进出次数要求
    ATTEND_TIME_REQUIRE = 8
    ACCESS_TIMES_LIMIT = 6
    # 默认波特率
    default_baudrates = 9600
    # 串口名或者实际port
    test_r_name = 'USB-SERIAL CH340'  # 测试电阻的串口名
    test_enter_card_name = 'USB Serial Port'  # 读卡的串口名
    test_r_port = ""  # 测试电阻的串口port
    test_enter_card_port = "COM3"  # 读卡的串口port
    # 串口命令
    hex_test_online = "01 01 01 00 00 00 00 01 CA"  # 测试是否在线
    hex_test_online_succcess = "01 01 01 00 00 00 00 05 AB"  # 测试是否在线成功
    hex_open_door = "01 01 04 00 00 00 00 01 21"  # 开门请求
    hex_open_door_success = "01 01 04 00 00 00 00 05 40 "  # 开门请求成功
    hex_get_cow = "01 01 03 00 00 00 00 01 A4"  # 测试电阻


# 测试配置，暂无用
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/edsystem'
    TESTING = True
