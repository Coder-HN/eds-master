import os
import pandas as pd
from io import BytesIO
from flask import send_file
from flask import Blueprint, request, jsonify, make_response, current_app
from werkzeug.utils import secure_filename

from config import Config
from mapper import UserMapper, DepartmentMapper, PositionMapper
from models import TableUser

"""
员工管理
/admin/manageUser：查询人员信息；上传人员数据、导入数据库；导出数据表；导出数据库；
"""
manageUser = Blueprint('manageUser', __name__, url_prefix='/api/admin/manageUser')


@manageUser.route('/getAllUsers', methods=['GET'])  # 获取人员表单
def get_all_users():
    try:
        all_users = UserMapper.get_all_users()
        users_list = [user.to_dict() for user in all_users]
        for user_dict in users_list:
            department_num = user_dict['department_num']
            position_num = user_dict['position_num']
            if department_num:
                department_name = (DepartmentMapper.get_department_by_num(int(department_num))).department_name
            else:
                department_name = ''
            if position_num:
                position_name = (PositionMapper.get_position_by_num(int(position_num))).position_name
            else:
                position_name = ''
            user_dict["department_name"] = department_name
            user_dict["position_name"] = position_name
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": users_list
    }
    return jsonify(response), 200


@manageUser.route('/searchUser', methods=['POST'])  # 添加人员
def search_user():
    employee_id = request.form.get('employee_id')
    card_id = request.form.get('card_id')
    name = request.form.get('name')
    department_num = request.form.get('department_num')
    position_num = request.form.get('position_num')
    try:
        all_users = UserMapper.get_users_by_multiple_conditions(employee_id, card_id, name, department_num,
                                                                position_num)
        users_list = [user.to_dict() for user in all_users]
        for user_dict in users_list:
            department_name = (DepartmentMapper.get_department_by_num(int(user_dict['department_num']))).department_name
            position_name = (PositionMapper.get_position_by_num(int(user_dict['position_num']))).position_name
            user_dict["department_name"] = department_name
            user_dict["position_name"] = position_name
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": users_list
    }
    return jsonify(response), 200


@manageUser.route('/deleteUser', methods=['POST'])  # 删除人员
def delete_user():
    data = request.get_json()
    num = data.get('num')
    is_change = UserMapper.update_user(num, TableUser(num=num, is_delete=1))
    if is_change:
        return make_response('', 200)
    else:
        return jsonify({'error': '删除人员失败'}), 500


@manageUser.route('/updateUser', methods=['POST'])  # 修改人员
def update_user():
    new_user = TableUser()
    # 处理其他数据
    num = request.form.get('num')
    new_user.num = num
    new_user.employee_id = request.form.get('employee_id')
    new_user.card_id = request.form.get('card_id')
    new_user.name = request.form.get('name')
    new_user.department_num = request.form.get('department_num')
    new_user.position_num = request.form.get('position_num')
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
            user = UserMapper.get_user_by_num(num)
            if user.pic_path:
                path_delete = Config.STATIC_PUBLIC + user.pic_path
                print(path_delete)
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
    if UserMapper.update_user(num, new_user):
        return make_response('', 200)
    else:
        return jsonify({'error': '更新数据失败'}), 500


@manageUser.route('/addUser', methods=['POST'])  # 添加人员
def add_user():
    new_user = TableUser()
    # 处理其他数据
    new_user.employee_id = request.form.get('employee_id')
    new_user.card_id = request.form.get('card_id')
    new_user.name = request.form.get('name')
    new_user.position_num = int(request.form.get('position_num'))
    new_user.department_num = int(request.form.get('position_num'))

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
        return jsonify({'error': '添加数据失败'}), 500


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
    try:
        # 使用 pandas 读取 Excel 文件
        df = pd.read_excel(file)
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
                # 处理
                department_num = None
                position_num = None
                if len(_department_name) > 0:
                    department = DepartmentMapper.get_department_by_name(_department_name)
                    department_num = department.num
                    if len(_position_name) > 0:
                        position_list = DepartmentMapper.get_position_by_department_num(department_num)
                        for position in position_list:
                            if position.position_name == _position_name:
                                position_num = position.num
                                break
                user_db = TableUser()
                user_db.employee_id = _employee_id
                user_db.card_id = _card_id
                user_db.name = _name
                user_db.department_num = department_num
                user_db.position_num = position_num
                user_get = UserMapper.get_user_by_employee_id(user_db.employee_id)
                if user_get:
                    if user_get.is_delete == 0:
                        UserMapper.update_user(user_get.num, TableUser(num=user_get.num, is_delete=1))
                        results.append({**row.to_dict(), '处理情况': '成功删除'})
                    else:
                        results.append({**row.to_dict(), '处理情况': '跳过、已删除'})
                else:
                    UserMapper.add_user(user_db)
                    results.append({**row.to_dict(), '处理情况': '成功添加'})
            except Exception as process_error:
                results.append({**row.to_dict(), '处理情况': f'失败: {str(process_error)}'})
        # 创建新的 DataFrame 并保存为 Excel 文件
        results_df = pd.DataFrame(results)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            results_df.to_excel(writer, index=False, sheet_name='处理结果')
        output.seek(0)

        # 这里设置 mimetype 为 Excel
        response = send_file(output, download_name='处理结果.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        return response, 200
    except Exception as e:
        current_app.logger.info(f"error: {str(e)}")
        return jsonify({'error': str(e)}), 500
