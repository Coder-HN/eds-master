class Config:
    # 本地数据库配置
    HOST = 'localhost'
    USER = 'root'
    PASSWORD = 'root'
    DATABASE = 'edsystem'
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 云端数据库配置
    INTERNET_SQL_Driver = '{SQL Server Native Client 11.0}'
    INTERNET_SQL_Server = '10.150.232.46'
    INTERNET_SQL_Database = 'DB_IASV4_KaiHong2023'
    INTERNET_SQL_USER = 'GateUser'
    INTERNET_SQL_PASSWORD = 'jR7#pW6%pH'

    # 开发环境
    # STATIC_PUBLIC = 'E:/workplaces/FrontProjects/edsFront/public'  # 静态文件位置
    # UPLOAD_FOLDER = 'E:/workplaces/FrontProjects/edsFront/public/profile_photo/'  # 头像位置
    # 部署环境
    STATIC_PUBLIC = 'D:/eds-front/public'  # 静态文件位置
    UPLOAD_FOLDER = 'D:/eds-front/public/profile_photo/'  # 头像位置

    # 在岗时间要求、进出次数要求
    ATTEND_TIME_REQUIRE = 8
    ACCESS_TIMES_LIMIT = 6

    # 默认波特率、端口超时时间ms
    default_baud_rate = 9600
    default_com_timeout = 3
    # 串口名
    test_r_port = "COM12"  # 测试电阻的串口port
    # test_enter_card_port = "COM3" # 读卡进门的串口port
    test_enter_card_port = "COM10"  # 串口测试用10->11
    # test_leave_card_port = "COM1" # 读卡出门的串口port
    test_leave_card_port = "COM7"  # 串口测试用7->8

    # 读卡02 + 卡号 +0D 0A 03
    card_start_data = 2
    card_end_data = bytes([0x0D, 0x0A, 0x03])
    # 串口命令
    hex_test_online = "01 01 01 00 00 00 00 01 CA"  # 测试是否在线
    hex_test_online_success = "01 01 01 00 00 00 00 05 AB"  # 测试是否在线成功
    hex_open_enter_door = "01 01 04 00 00 00 00 01 21"  # 进门开门请求
    hex_open_leave_door = "01 01 04 00 00 00 01 01 E5"  # 出门开门请求
    hex_open_enter_door_success = "01 01 04 00 00 00 00 05 40 "  # 进门开门请求成功
    hex_open_leave_door_success = "01 01 04 00 00 00 01 05 84 "  # 出门开门请求成功
    hex_get_cow = "01 01 03 00 00 00 00 01 A4"  # 测试电阻
    # 校准电阻指令直接定义在testResistanceHelper.py的方法中


# 测试配置，暂时无用
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/edsystem'
    TESTING = True
