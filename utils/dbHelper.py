import glob
import os
import subprocess
from datetime import datetime, timedelta
from io import BytesIO

import mysql.connector

from config import Config
from utils.loggingHelper import log_message

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
        log_message(f"Error: {e}", 'warning')


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
                log_message(f"Error: {stderr.decode('utf-8')}", 'warning')
                return None
            # 将导出的数据库内容写入 BytesIO 流
            output.write(stdout)
            output.seek(0)  # 重置流位置，准备读取
        return output
    except subprocess.CalledProcessError as e:
        log_message(f"Error: {e}", 'warning')
        return None



def get_user_by_num(num):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_user WHERE num = '{num}'"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_user_by_card_id(card_id):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM table_user WHERE card_id = %s AND is_delete = 0"
    cursor.execute(query, (card_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_user_by_card_id_all(card_id):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_user WHERE card_id = '{card_id}'"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_user_by_employee_id(employee_id):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_user WHERE employee_id ='{employee_id}'"
    cursor.execute(query)
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


def get_department_by_name(department_name):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_department WHERE department_name = '{department_name}'"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def add_department(department_name):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"INSERT INTO table_department (department_name) VALUES ('{department_name}')"
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_department WHERE department_name = '{department_name}'"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_position_by_name(position_name):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_position WHERE position_name = '{position_name}'"

    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def add_position(position_name):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"INSERT INTO table_position (position_name) VALUES ('{position_name}')"
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()

    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_position WHERE position_name = '{position_name}'"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_department_by_position_num(position_num):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_department_position WHERE position_num = {position_num}"
    cursor.execute(query)
    department_num_list = []
    row = cursor.fetchone()
    while row:
        department_num_list.append(row['department_num'])
        row = cursor.fetchone()
    cursor.close()
    conn.close()
    return department_num_list


def add_position_department(position_num, department_num):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"INSERT INTO table_department_position (position_num,department_num) VALUES ({position_num},{department_num})"
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()


def get_service_by_num(service_num):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_service WHERE num = {service_num}"
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


# 修改员工信息or删除员工（将is_delete置为1）
def update_user(user_num, userInfo):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    if 'pic_path' in userInfo:
        query = f'''update table_user SET 
            employee_id='{userInfo['employee_id']}',
            card_id='{userInfo['card_id']}',
            name='{userInfo['name']}',
            position_num={userInfo['position_num']},
            department_num={userInfo['department_num']},
            pic_path='{userInfo['pic_path']}',
            is_delete={userInfo['is_delete']} WHERE num={user_num}'''
        cursor.execute(query)
    else:
        query = f'''update table_user SET 
            employee_id='{userInfo['employee_id']}',
            card_id='{userInfo['card_id']}',
            name='{userInfo['name']}',
            position_num={userInfo['position_num']},
            department_num={userInfo['department_num']},
            is_delete={userInfo['is_delete']} WHERE num={user_num}'''
        cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()


def add_user(userInfo):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    if 'pic_path' in userInfo:
        query = f'''INSERT INTO table_user (
            employee_id,
            card_id,
            name,
            position_num,
            department_num,
            pic_path,
            is_delete) VALUES ('{userInfo['employee_id']}',
                        '{userInfo['card_id']}',
                        '{userInfo['name']}',
                        {userInfo['position_num']},
                        {userInfo['department_num']},
                        '{userInfo['pic_path']}',
                        {userInfo['is_delete']})'''
        cursor.execute(query)
    else:
        query = f'''INSERT INTO table_user (
            employee_id,
            card_id,
            name,
            position_num,
            department_num,
            is_delete) VALUES ('{userInfo['employee_id']}',
                        '{userInfo['card_id']}',
                        '{userInfo['name']}',
                        {userInfo['position_num']},
                        {userInfo['department_num']},
                        {userInfo['is_delete']})'''
        cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()


def get_all_access_by_time():
    # 计算当前时间减去20分钟的时间点
    time_threshold = datetime.now() - timedelta(minutes=20)
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)
    query = f"SELECT * FROM table_access WHERE access_time >= '{time_threshold}' ORDER BY access_time asc"
    cursor.execute(query)
    all_access = []
    row = cursor.fetchone()
    while row:
        all_access.append(row)
        row = cursor.fetchone()
    cursor.close()
    conn.close()
    return all_access


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
