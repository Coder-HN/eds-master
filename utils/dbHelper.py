import glob
import os
import subprocess
from io import BytesIO

import mysql.connector

from config import Config

# 读取MySQL数据库配置
mysql_config = {
    'host': Config.HOST,
    'user': Config.USER,
    'password': Config.PASSWORD,
    'database': Config.DATABASE
}


# 清理sql文件
def delete_sql_files_in_folder(folder_path):
    try:
        # 使用 glob 模块匹配所有 .sql 文件
        sql_files = glob.glob(os.path.join(folder_path, '*.sql'))
        for file_path in sql_files:
            os.remove(file_path)  # 删除 .sql 文件
    except Exception as e:
        print(f"Error: {e}")


# 导出MySQL数据库到SQL文件
def export_mysql_to_sql():
    output = BytesIO()
    command = [
        "mysqldump",
        "-h", mysql_config['host'],
        "-u", mysql_config['user'],
        f"-p{mysql_config['password']}",
        mysql_config['database']
    ]

    try:
        # 使用 subprocess.Popen 执行 mysqldump 命令
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                print(f"Error: {stderr.decode('utf-8')}")
                return None
            # 将导出的数据库内容写入 BytesIO 流
            output.write(stdout)
            output.seek(0)  # 重置流位置，准备读取
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None


# TODO 导入SQL文件到MySQL数据库


def get_user_by_card_id(card_id):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM table_user WHERE card_id = %s AND is_delete = 0"
    cursor.execute(query, (card_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_department_by_num(department_num):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM table_department WHERE num = %s"
    cursor.execute(query, (department_num,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_test_standard_by_service_id(service_id):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM table_service WHERE service_id = %s"
    cursor.execute(query, (service_id,))
    service = cursor.fetchone()

    r_num = service['r_standard_num']
    test_part = service['test_part']

    query = "SELECT * FROM table_r_standard WHERE num = %s"
    cursor.execute(query, (r_num,))
    r_standard = cursor.fetchone()
    cursor.close()
    conn.close()
    return {
        'test_part': test_part,

        'hand_left_min': float(r_standard['hand_left_min']),
        'hand_left_max': float(r_standard['hand_left_max']),
        'hand_right_min': float(r_standard['hand_right_min']),
        'hand_right_max': float(r_standard['hand_right_max']),
        'foot_left_min': float(r_standard['foot_left_min']),
        'foot_left_max': float(r_standard['foot_left_max']),
        'foot_right_min': float(r_standard['foot_right_min']),
        'foot_right_max': float(r_standard['foot_right_max']),
    }
