from flask import Blueprint, jsonify
from config import Config
import mapper.AccessMapper as AccessMapper
import mapper.DepartmentMapper as DepartmentMapper
import mapper.PositionMapper as PositionMapper
import mapper.ServiceMapper as ServiceMapper
import mapper.UserMapper as UserMapper
import pyodbc
import io
from PIL import Image
import time
from datetime import datetime

"""
网络数据同步
/api
/inter/sync_user_data
/inter/sync_local_records
"""
inter = Blueprint('inter', __name__, url_prefix='/api/inter')

conn_str = (
    f"Driver={Config.INTERNET_SQL_Driver};"
    f"Server={Config.INTERNET_SQL_Server};"
    f"Database={Config.INTERNET_SQL_Database};"
    f"UID={Config.INTERNET_SQL_USER};"
    f"PWD={Config.INTERNET_SQL_PASSWORD};"
)


# 同步云端用户信息数据
@inter.route('/sync_user_data', methods=['GET'])
def update_cloud_userinfo_to_local_router():
    is_hand_opera = True
    return update_cloud_userinfo_to_local(is_hand_opera)


def update_cloud_userinfo_to_local(is_hand_opera=False):
    print("in update_cloud_userinfo_to_local")
    msg = ""
    handleCnt = 0
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        if is_hand_opera:
            query = "SELECT * FROM vw_employee order by updatetime asc"
            # is_hand_opera=False
        else:
            query = "SELECT * FROM vw_employee WHERE updatetime > DATEADD(day, -1, GETDATE()) order by updatetime asc"
        cursor.execute(query)
        rowline = cursor.fetchone()
        while rowline:
            row = dict(zip([col[0] for col in cursor.description], rowline))
            isHavePhoto = 0
            # Handle Photo
            data = row['empimage']
            print(row['empcode'])
            # print (row.empimage)
            if data == "" or data == b' ':
                print("Empty Picture")
            else:
                isHavePhoto = 1
                print("Save Photo to File")
                photoname = f"{row['empcode']}_{row['CARDNO']}.jpg"
                image = Image.open(io.BytesIO(data))
                path = "D:\\eds-front\\public\\profile_photo\\" + photoname
                image.convert('RGB').save(path, 'JPEG', quality=95)
            # employee_id
            _employee_id = row['empcode']
            # card_id
            _card_id = row['CARDNO']
            # name
            _name = row['empname']

            # _department_name
            _department_id = row['deptid']
            conn1 = pyodbc.connect(conn_str)
            cursor1 = conn1.cursor()
            # print(f"SELECT * FROM vw_department where deptid='{_department_id}'")
            cursor1.execute(f"SELECT * FROM vw_department where deptid='{_department_id}'")
            rowline1 = cursor1.fetchone()
            if rowline1:
                row1 = dict(zip([col[0] for col in cursor1.description], rowline1))
                _department_name = row1['deptname']
            else:
                _department_name = '无相关部门'
            cursor1.close()
            conn1.close()

            # _position_name
            _position_name = f"{_department_name}_1"

            # users_employee_id_excel.append(_employee_id)
            # users_card_id_excel.append(_card_id)
            user_get = None
            user_get_employee_id = UserMapper.get_user_by_employee_id(_employee_id)
            user_get_card_id = UserMapper.get_user_by_card_id(_card_id)
            # if user_get_employee_id is not None:
            #     user_get = user_get_employee_id
            # elif user_get_card_id is not None:
            #     user_get = user_get_card_id
            if user_get_employee_id is not None:
                user_get = user_get_employee_id
            if user_get_card_id is not None:
                user_get = user_get_card_id
            if user_get is not None:  # 数据库原来有
                print(f"{_employee_id}:信息需要更新:{_card_id}")
                department_num, position_num = handle_dp(_department_name, _position_name)
                userInfo = {'employee_id': '0', 'card_id': '0'}
                userInfo['employee_id'] = _employee_id
                userInfo['card_id'] = _card_id
                userInfo['name'] = _name
                userInfo['position_num'] = position_num
                userInfo['department_num'] = department_num
                if isHavePhoto == 1:
                    userInfo['pic_path'] = "/profile_photo/" + photoname
                if row['empstatus'] == 'A1':
                    userInfo['is_delete'] = 0
                elif row['empstatus'] == 'A0':
                    userInfo['is_delete'] = 1
                if row['canpass'] == '1':
                    userInfo['is_delete'] = 0
                elif row['canpass'] == '0':
                    userInfo['is_delete'] = 1
                UserMapper.update_user(user_get['num'], userInfo)
                print(f"{_employee_id}:信息已更新")
            else:  # 数据库原来没有
                print(f"{_employee_id}:信息需要添加")
                department_num, position_num = handle_dp(_department_name, _position_name)
                userInfo = {'employee_id': '0', 'card_id': '0'}
                userInfo['employee_id'] = _employee_id
                userInfo['card_id'] = _card_id
                userInfo['name'] = _name
                userInfo['position_num'] = position_num
                userInfo['department_num'] = department_num
                if isHavePhoto == 1:
                    userInfo['pic_path'] = "/profile_photo/" + photoname
                if row['empstatus'] == 'A1':
                    userInfo['is_delete'] = 0
                elif row['empstatus'] == 'A0':
                    userInfo['is_delete'] = 1
                if row['canpass'] == '1':
                    userInfo['is_delete'] = 0
                elif row['canpass'] == '0':
                    userInfo['is_delete'] = 1
                UserMapper.add_user(userInfo)
                print(f"{_employee_id}:成功添加")
                # results.append({**row.to_dict(), '处理情况': '成功添加'})
            handleCnt = handleCnt + 1
            print(f"HandleCnt:{handleCnt}")
            time.sleep(0.001)
            rowline = cursor.fetchone()
            msg = f"[{datetime.now()}] 成功同步 {handleCnt} 条云端员工数据到本地"
        return jsonify({'status': 'success', 'message': msg}), 200
    except Exception as e:
        msg = f'更新云端员工数据到本地失败: {str(e)}'
        return jsonify({'status': 'error', 'message': msg}), 500
    finally:
        print(msg)


# 本地进出记录同步到云端
@inter.route('/sync_local_records', methods=['GET'])
def update_local_access_to_cloud_router():
    return update_local_access_to_cloud()


def update_local_access_to_cloud():
    print("in update_local_access_to_cloud")
    msg = ""
    try:
        conn = pyodbc.connect(conn_str)
        access_list = AccessMapper.get_all_access_by_time()
        for access in access_list:
            user_num = access.user_num
            user = UserMapper.get_user_by_num(user_num)
            access['name'] = user.name
            # empcode
            access['empcode'] = user.employee_id
            # cardno
            access['cardno'] = user.card_id
            # deptid
            department = DepartmentMapper.get_department_by_num(user.department_num)
            # -deptname
            access['deptname'] = department.department_name
            # deptid
            cursorDept = conn.cursor()
            query = f"SELECT * FROM vw_department where deptname='{access['deptname']}'"
            cursorDept.execute(query)
            rowDept = cursorDept.fetchone()
            access['deptid'] = rowDept.deptid
            # devicetype
            access['devicetype'] = 2
            # gateid
            service = ServiceMapper.get_service_by_num(access["service_num"])
            # -devicename
            access['service_name'] = service.service_name
            # get from sql server: select * from vw_device_gate where devicename={access['service_name']}
            cursor = conn.cursor()
            query = f"SELECT * FROM vw_device_gate where devicename='{access['service_name']}'"
            print(query)
            cursor.execute(query)
            row = cursor.fetchone()
            access['gateid'] = row.deviceid
            # recordtime
            access['recordtime'] = access['access_time']
            # recordmode
            if access['access_flag'] == 1:
                access['recordmode'] = "in"
            else:
                access['recordmode'] = "out"

            # testresult
            if access['result'] == 1:
                access['testresult'] = 1
            else:
                access['testresult'] = 0

            # testvalue
            if access['value_hand_left'] == -1:
                access['value_hand_left'] = "未测"
            elif access['value_hand_left'] is not None:
                access['value_hand_left'] = str(access['value_hand_left']) + "KΩ"

            if access['value_hand_right'] == -1:
                access['value_hand_right'] = "未测"
            elif access['value_hand_right'] is not None:
                access['value_hand_right'] = str(access['value_hand_right']) + "KΩ"

            if access['value_foot_left'] == -1:
                access['value_foot_left'] = "未测"
            elif access['value_foot_left'] is not None:
                access['value_foot_left'] = str(access['value_foot_left']) + "KΩ"

            if access['value_foot_right'] == -1:
                access['value_foot_right'] = "未测"
            elif access['value_foot_right'] is not None:
                access['value_foot_right'] = str(access['value_foot_right']) + "KΩ"
            access[
                'testvalue'] = f"{access['value_hand_left']},{access['value_hand_right']},{access['value_foot_left']},{access['value_foot_right']}"

            # Check if record exist
            cursorRecordCheck = conn.cursor()
            query = f"SELECT COUNT(*) AS CNT FROM tbl_accessgaterecord where empcode='{access['empcode']}' and gateid='{access['gateid']}' and recordtime='{access['recordtime']}'"
            print(query)
            cursorRecordCheck.execute(query)
            rowCnt = cursorRecordCheck.fetchone()
            row_count = rowCnt.CNT
            # Insert Record
            if row_count == 0:
                cursorRecordInsert = conn.cursor()
                insertSql = f'''INSERT INTO tbl_accessgaterecord (empcode,deptid,cardno,devicetype,gateid,recordtime,recordmode,testresult,testvalue) VALUES (
                            '{access['empcode']}',
                            '{access['deptid']}',
                            '{access['cardno']}',
                            '{access['devicetype']}',
                            '{access['gateid']}',
                            '{access['recordtime']}',
                            '{access['recordmode']}',
                            '{access['testresult']}',
                            '{access['testvalue']}')'''
                print(insertSql)
                cursorRecordInsert.execute(insertSql)
                conn.commit()
        msg += f"[{datetime.now()}] 成功同步 {len(access_list)} 条本地进出记录到云端"
        return jsonify({'status': 'success', 'message': msg}), 200
    except Exception as e:
        msg += f'同步失败: {str(e)}'
        return jsonify({'status': 'error', 'message': msg}), 500
    finally:
        print(msg)


def handle_dp(_department_name, _position_name):
    # 处理
    department_num = None
    position_num = None
    # 查看部门
    if len(_department_name) > 0:
        department = DepartmentMapper.get_department_by_name(_department_name)
        if department is not None:  # 已经存在该部门
            department_num = department.num
        else:
            new_department = DepartmentMapper.add_department(_department_name)
            if new_department:  # 不存在该部门则重新创建并创建
                department_num = new_department.num
    # 查看职位
    if len(_position_name) > 0:  # 在position表中查找是否存在该职位
        position = PositionMapper.get_position_by_name(_position_name)
        if position is not None:
            position_num = position.num
        else:
            new_position = PositionMapper.add_position(_position_name)
            position_num = new_position.num
    # 查看部门职位关系
    department_num_list = DepartmentMapper.get_department_by_position_num(position_num)
    if department_num not in department_num_list:
        PositionMapper.add_position_department(position_num, department_num)
    return department_num, position_num
