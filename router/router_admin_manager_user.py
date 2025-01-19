import os
import sys

import pandas as pd
from io import BytesIO
from flask import send_file
from flask import Blueprint, request, jsonify, make_response, current_app
from werkzeug.utils import secure_filename

from config import Config
from mapper import UserMapper, DepartmentMapper, PositionMapper
from mapper.UserMapper import is_exist
from models import TableUser

"""
员工管理
/admin/manageUser：查询人员信息；上传人员数据、导入数据库；导出数据表；导出数据库；
"""
manageUser = Blueprint('manageUser', __name__, url_prefix='/api/admin/manageUser')


@manageUser.route('/getAllUsers', methods=['GET'])  # 查询人员
def get_all_users():
    try:
        # 获取分页参数
        page = int(request.args.get('page', 1))  # 当前页码，默认为第 1 页
        page_size = int(request.args.get('pageSize', 5))  # 每页记录数，默认为 5 条
        # 计算分页的起始索引和结束索引
        offset = (page - 1) * page_size
        limit = page_size
        request_type = request.args.get('type')
        all_users = []
        total_records = 0
        if request_type == '1':  # 普通权限，只能看到在职人员
            total_records = UserMapper.get_users_count()  # 获取总记录数
            all_users = UserMapper.get_users_paginated(offset, limit)  # 获取分页后的记录
        elif request_type == '2':
            total_records = UserMapper.get_all_users_count()  # 获取总记录数
            all_users = UserMapper.get_all_users_paginated(offset, limit)  # 获取分页后的记录
        users_list = [user.to_dict() for user in all_users]
        for user_dict in users_list:
            department_num = user_dict['department_num']
            position_num = user_dict['position_num']
            department_name = ''
            position_name = ''
            if department_num:
                department_name = (DepartmentMapper.get_department_by_num(int(department_num))).department_name
            if position_num:
                position_name = (PositionMapper.get_position_by_num(int(position_num))).position_name
            user_dict["department_name"] = department_name
            user_dict["position_name"] = position_name
        response = {
            "data": users_list,
            "pagination": {
                "current": page,
                "pageSize": page_size,
                "total": total_records,
            }
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@manageUser.route('/searchUser', methods=['POST'])  # 搜索人员
def search_user():
    try:
        request_type = request.form.get('type')
        employee_id = request.form.get('employee_id')
        card_id = request.form.get('card_id')
        name = request.form.get('name')
        department_num = request.form.get('department_num')
        position_num = request.form.get('position_num')
        all_users = UserMapper.get_users_by_multiple_conditions(request_type, employee_id,
                                                                card_id, name,
                                                                department_num, position_num)
        users_list = [user.to_dict() for user in all_users]
        for user_dict in users_list:
            department_num = user_dict['department_num']
            position_num = user_dict['position_num']
            department_name = ''
            position_name = ''
            if department_num:
                department_name = (DepartmentMapper.get_department_by_num(int(department_num))).department_name
            if position_num:
                position_name = (PositionMapper.get_position_by_num(int(position_num))).position_name
            user_dict["department_name"] = department_name
            user_dict["position_name"] = position_name
        response = {
            "data": users_list
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': e}), 500


@manageUser.route('/deleteUser', methods=['POST'])  # 删除人员
def delete_user():
    data = request.get_json()
    num = data.get('num')
    is_change = UserMapper.update_user(num, TableUser(num=num, is_delete=1))
    if is_change:
        return make_response('', 200)
    else:
        return jsonify({'error': '删除人员失败'}), 500


@manageUser.route('/recoverUser', methods=['POST'])  # 删除人员
def recover_user():
    data = request.get_json()
    num = data.get('num')
    is_change = UserMapper.update_user(num, TableUser(num=num, is_delete=0))
    if is_change:
        return make_response('', 200)
    else:
        return jsonify({'error': '恢复人员失败'}), 500


@manageUser.route('/updateUser', methods=['POST'])  # 修改人员
def update_user():
    employee_id = request.form.get('employee_id')
    card_id = request.form.get('card_id')
    num = int(request.form.get('num'))
    _, msg, list_user_num = is_exist(employee_id, card_id)
    res = False
    msg_zh = ""
    for i in range(len(list_user_num)):
        if list_user_num[i] != num:
            res = True
            msg_zh += msg[i]
    if res:
        return jsonify({'error': msg_zh}), 201
    else:
        new_user = TableUser()
        # 处理数据
        new_user.num = num
        new_user.employee_id = employee_id
        new_user.card_id = card_id
        new_user.name = request.form.get('name')
        position_num = request.form.get('position_num')
        if position_num is not None:
            new_user.position_num = int(position_num)

        department_num = request.form.get('department_num')
        if department_num is not None:
            new_user.department_num = int(department_num)

        # 处理头像
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '没有选择文件'}), 400
            mime_type = file.content_type
            if mime_type not in ['image/jpeg', 'image/png']:
                return jsonify({'error': '不支持的文件类型'}), 415
            if file:
                # 要先删除原来的图像
                user = UserMapper.get_user_by_num(new_user.num)
                if user.pic_path:
                    path_delete = Config.STATIC_PUBLIC + user.pic_path
                    if os.path.exists(path_delete):
                        os.remove(path_delete)
                filename = secure_filename(file.filename)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                file.save(file_path)
                new_file_name = f"{new_user.employee_id}_{new_user.card_id}.jpg"
                new_file_path = os.path.join(Config.UPLOAD_FOLDER, new_file_name)
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                os.rename(file_path, new_file_path)
                file_url = f'/profile_photo/{new_file_name}'
                new_user.pic_path = file_url
        if UserMapper.update_user(new_user.num, new_user):
            return make_response('', 200)
        else:
            return jsonify({'error': 'UserMapper.update_user更新数据失败'}), 500


@manageUser.route('/addUser', methods=['POST'])  # 添加人员
def add_user():
    employee_id = request.form.get('employee_id')
    card_id = request.form.get('card_id')
    res, msg, _ = is_exist(employee_id, card_id)
    msg_zh = ""
    for m in msg:
        msg_zh += m
    if res:
        return jsonify({'error': msg_zh}), 201
    else:
        # 处理数据
        new_user = TableUser()
        new_user.employee_id = employee_id
        new_user.card_id = card_id
        new_user.name = request.form.get('name')

        position_num = request.form.get('position_num')
        if position_num is not None:
            new_user.position_num = int(position_num)

        department_num = request.form.get('department_num')
        if department_num is not None:
            new_user.department_num = int(department_num)

        # 处理头像
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '没有选择文件'}), 400
            mime_type = file.content_type
            if mime_type not in ['image/jpeg', 'image/png']:
                return jsonify({'error': '不支持的文件类型'}), 415
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                file.save(file_path)
                new_file_name = f"{new_user.employee_id}_{new_user.card_id}.jpg"
                new_file_path = os.path.join(Config.UPLOAD_FOLDER, new_file_name)
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                os.rename(file_path, new_file_path)
                file_url = f'/profile_photo/{new_file_name}'
                new_user.pic_path = file_url
        if UserMapper.add_user(new_user):
            return make_response('', 200)
        else:
            return jsonify({'error': 'UserMapper.add_user添加数据失败'}), 500


@manageUser.route('/addUserExcel', methods=['POST'])  # 添加人员表
def add_user_excel():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 200
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 200
    mime_type = file.content_type
    if mime_type not in ['application/vnd.ms-excel',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
        return jsonify({'error': '文件类型不支持，请上传Excel文件'}), 200
    users_employee_id_excel = []
    users_card_id_excel = []
    try:
        # 使用 pandas 读取 Excel 文件，使用 `dtype` 参数将 card_id，employee_id 列读取为字符串类型
        df = pd.read_excel(file, dtype={
            'card_id': str,
            'employee_id': str,
        })
        results = []  # 存储处理结果
        # 遍历每一行，创建 UserExcelMessage 实例
        for _, row in df.iterrows():
            _employee_id = row['employee_id']
            if pd.isna(_employee_id):
                _employee_id = ""

            _card_id = row['card_id']
            if pd.isna(_card_id):
                _card_id = ""

            _name = row['name']
            if pd.isna(_name):
                _name = ""

            _department_name = row['department_name']
            if pd.isna(_department_name):
                _department_name = ""

            _position_name = row['position_name']
            if pd.isna(_position_name):
                _position_name = ""

            try:
                if _employee_id == "" or _card_id == "":
                    results.append({**row.to_dict(), '处理情况': '没有工号或卡号、跳过'})
                else:
                    users_employee_id_excel.append(_employee_id)
                    users_card_id_excel.append(_card_id)
                    user_get = None
                    user_get_employee_id = UserMapper.get_user_by_employee_id(_employee_id)
                    user_get_card_id = UserMapper.get_user_by_card_id(_card_id)
                    if user_get_employee_id is not None:
                        user_get = user_get_employee_id
                    elif user_get_card_id is not None:
                        user_get = user_get_card_id
                    if user_get is not None:  # 数据库原来有
                        if user_get.is_delete == 1:
                            UserMapper.update_user(user_get.num, TableUser(num=user_get.num, is_delete=0))
                            results.append({**row.to_dict(), '处理情况': '数据库中已删除、复原'})
                        else:
                            results.append({**row.to_dict(), '处理情况': '数据库中已存在相同工号或卡号、跳过'})
                    else:  # 数据库原来没有
                        department_num, position_num = handle_dp(_department_name, _position_name)
                        user_db = TableUser()
                        user_db.employee_id = _employee_id
                        user_db.card_id = _card_id
                        user_db.name = _name
                        user_db.department_num = department_num
                        user_db.position_num = position_num
                        UserMapper.add_user(user_db)
                        results.append({**row.to_dict(), '处理情况': '成功添加'})

            except Exception as process_error:
                results.append({**row.to_dict(), '处理情况': f'失败: {str(process_error)}'})
        # 在Excel中不存在，而数据库中有的，将该员工从当前表中移至离职人员表中，但进出记录需要保存，可查询
        users_db = UserMapper.get_all_users()
        for user_db in users_db:
            # 存在excel表中
            if user_db.employee_id not in users_employee_id_excel and user_db.card_id not in users_card_id_excel:
                UserMapper.update_user(user_db.num, TableUser(num=user_db.num, is_delete=1))

        # 创建新的 DataFrame 并保存为 Excel 文件
        results_df = pd.DataFrame(results)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            results_df.to_excel(writer, index=False, sheet_name='处理结果')
        output.seek(0)

        # 这里设置 mimetype 为 Excel
        response = send_file(output, download_name='处理结果.xlsx', as_attachment=True,
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        return response, 200
    except Exception as e:
        exc_info = sys.exc_info()
        current_app.log_exception(exc_info)
        current_app.logger.error(f"error: {str(e)}")
        return jsonify({'error': str(e)}), 500


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


@manageUser.route('/exportUserExcel', methods=['POST'])  # 导出人员表
def export_user_excel():
    try:
        # 从数据库中获取用户数据（根据搜索情况）
        request_type = request.form.get('type')
        employee_id = request.form.get('employee_id')
        card_id = request.form.get('card_id')
        name = request.form.get('name')
        department_num = request.form.get('department_num')
        position_num = request.form.get('position_num')
        all_users = UserMapper.get_users_by_multiple_conditions(request_type, employee_id,
                                                                card_id, name,
                                                                department_num, position_num)
        # 将数据库中的数据转换为字典格式
        user_data = []
        for user in all_users:
            user_data.append({
                'employee_id': user.employee_id,
                'card_id': user.card_id,
                'name': user.name,
                'department_name': DepartmentMapper.get_department_by_num(
                    user.department_num).department_name if user.department_num else "",
                'position_name': PositionMapper.get_position_by_num(
                    user.position_num).position_name if user.position_num else "",
                'is_delete': user.is_delete
            })
        # 使用 pandas 将数据转换为 DataFrame
        df = pd.DataFrame(user_data)
        # 创建输出流，用于生成 Excel 文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # 将 DataFrame 写入 Excel 文件，保持与导入格式一致的列
            df.to_excel(writer, index=False, sheet_name='用户数据')
            # 获取 worksheet 对象
            worksheet = writer.sheets['用户数据']
            # 设置列宽仅根据列名长度
            for idx, col in enumerate(df.columns):  # 遍历 DataFrame 的每一列
                worksheet.set_column(idx, idx, len(col) + 2)  # 根据列名长度设置列宽，加 2 以增加空白
        output.seek(0)  # 将指针移到文件开头

        # 返回生成的 Excel 文件
        return send_file(output,
                         download_name='用户数据.xlsx',
                         as_attachment=True,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        # 记录并返回错误信息
        current_app.logger.error(f"Error exporting user Excel: {str(e)}")
        return jsonify({'error': str(e)}), 500
