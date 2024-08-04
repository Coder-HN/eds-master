import os

from flask import Blueprint, request, jsonify, make_response, current_app
from werkzeug.utils import secure_filename

from config import Config
from mapper import UserMapper
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
    department = request.form.get('department')
    position = request.form.get('position')
    try:
        all_users = UserMapper.get_users_by_multiple_conditions(employee_id, card_id, name, department, position)
        users_list = [user.to_dict() for user in all_users]
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
    new_user.department = request.form.get('department')
    new_user.position = request.form.get('position')
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
            new_file_name = f"{new_user.employee_id}_{new_user.name}.jpg"
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
    new_user.department = request.form.get('department')
    new_user.position = request.form.get('position')
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
            new_file_name = f"{new_user.employee_id}_{new_user.name}.jpg"
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


# TODO 导出人员信息
@manageUser.route('/downloadUser', methods=['POST'])  # 导出人员
def download_user():
    return make_response('', 200)
