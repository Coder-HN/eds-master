import json

from flask import Blueprint, request, jsonify, make_response

from mapper import DepartmentMapper, PositionMapper
from models import TableDepartment, TablePosition

"""
部门管理
/admin/manageDepartment：上传部门信息；设置部门名称
"""
manageDepartment = Blueprint('manageDepartment', __name__, url_prefix='/api/admin/manageDepartment')


class DepartmentMessage:
    def __init__(self, _department, _position_count, _list_position):
        self.department = _department
        self.position_count = _position_count
        self.list_position = _list_position

    def to_dict(self):
        return {
            'department': self.department,
            'position_count': self.position_count,
            'list_position': self.list_position
        }


@manageDepartment.route('/getAllDepartments', methods=['GET'])  # 获取所有部门及职位
def get_all_departments():
    message_list_dict = []
    try:
        all_departments = DepartmentMapper.get_all_departments()
        departments_list = [Department.to_dict() for Department in all_departments]
    except Exception as e:
        return jsonify({'error': '获取所有部门失败: ' + str(e)}), 500
    try:
        for department in departments_list:
            list_position = DepartmentMapper.get_position_by_department_num(int(department['num']))
            list_position_json = json.dumps([position.to_dict() for position in list_position], ensure_ascii=False)
            position_count = len(list_position)
            message = DepartmentMessage(department, position_count, list_position_json)
            message_list_dict.append(message.to_dict())
    except Exception as e:
        return jsonify({'error': '获取部门职位失败: ' + str(e)}), 500
    # 创建响应体
    response = {
        "data": message_list_dict
    }
    return jsonify(response), 200


@manageDepartment.route('/getDepartments', methods=['GET'])  # 获取所有部门
def get_departments():
    try:
        all_departments = DepartmentMapper.get_all_departments()
        departments_list = [Department.to_dict() for Department in all_departments]
    except Exception as e:
        return jsonify({'error': '获取所有部门失败: ' + str(e)}), 500
    # 创建响应体
    response = {
        "data": departments_list
    }
    return jsonify(response), 200


@manageDepartment.route('/getPositions', methods=['GET'])  # 获取指定部门所有职位
def get_positions():
    try:
        department_num = request.args.get('department_num')
        all_positions = DepartmentMapper.get_position_by_department_num(department_num)
        position_list = [Position.to_dict() for Position in all_positions]
    except Exception as e:
        return jsonify({'error': '获取该部门职位失败: ' + str(e)}), 500
    # 创建响应体
    response = {
        "data": position_list
    }
    return jsonify(response), 200


@manageDepartment.route('/addDepartment', methods=['POST'])  # 添加部门
def add_department():
    new_department = TableDepartment()
    # 处理其他数据
    new_department.department_name = request.form.get('department_name')
    if DepartmentMapper.add_department(new_department):
        return make_response('', 200)
    else:
        return jsonify({'error': '添加数据失败'}), 500


@manageDepartment.route('/addPosition', methods=['POST'])  # 添加部门
def add_position():
    new_position = TablePosition()
    # 处理其他数据
    department_num = int(request.form.get('department_num'))
    new_position.position_name = request.form.get('position_name')
    position = PositionMapper.add_position(new_position)
    if position:
        if PositionMapper.add_position_department(position_num=position.num, department_num=department_num):
            return make_response('', 200)
        else:
            return jsonify({'error': '添加部门职位关系数据失败'})
    else:
        return jsonify({'error': '添加职位数据失败'}), 500


@manageDepartment.route('/searchDepartment', methods=['POST'])  # 搜索部门
def search_departments():
    try:
        status = 200
        position_name = request.form.get('position_name')
        department_name = request.form.get('department_name')
        if position_name is None and department_name is None:
            return get_all_departments()
        message_list_dict = []
        all_department_nums = []
        if position_name is not None:
            position = PositionMapper.get_position_by_name(position_name)
            if position is not None:
                department_num_list = DepartmentMapper.get_department_by_position_num(position.num)
                all_department_nums.append(department_num_list)
        if department_name is not None:
            department = DepartmentMapper.get_department_by_name(department_name)
            if department is not None:
                if department.num in all_department_nums:  # 找到了唯一一个
                    all_department_nums.clear()
                    all_department_nums.append(department.num)
                elif position_name:
                    status = 201
        all_departments = []
        for department_num in all_department_nums:
            department = DepartmentMapper.get_department_by_num(department_num)
            all_departments.append(department)
        departments_list = [Department.to_dict() for Department in all_departments]
        for department in departments_list:
            list_position = DepartmentMapper.get_position_by_department_num(int(department['num']))
            list_position_json = json.dumps([position.to_dict() for position in list_position], ensure_ascii=False)
            position_count = len(list_position)
            message = DepartmentMessage(department, position_count, list_position_json)
            message_list_dict.append(message.to_dict())
        # 创建响应体
        response = {
            "data": message_list_dict
        }
        return jsonify(response), status
    except Exception as e:
        return jsonify({'error': '获取部门职位失败: ' + str(e)}), 500


@manageDepartment.route('/deleteDepartment', methods=['POST'])  # 删除部门
def delete_department():
    try:
        data = request.get_json()
        department_num = data.get('num')
        is_change = DepartmentMapper.delete_department_complex(department_num)
        if is_change:
            return make_response('', 200)
        else:
            return jsonify({'error': '删除部门失败'}), 500
    except Exception as e:
        return jsonify({'error': '删除部门失败: ' + str(e)}), 500


@manageDepartment.route('/deletePosition', methods=['POST'])  # 删除职位
def delete_position():
    try:
        data = request.get_json()
        position_num = data.get('num')
        department_num = data.get('department_num')
        is_change = PositionMapper.delete_position_complex(position_num=position_num, department_num=department_num)
        if is_change:
            return make_response('', 200)
        else:
            return jsonify({'error': '删除职位失败'}), 500
    except Exception as e:
        return jsonify({'error': '删除职位失败: ' + str(e)}), 500


@manageDepartment.route('/updateDepartment', methods=['POST'])  # 删除部门
def update_department():
    try:
        data = request.get_json()
        department_num = data.get('num')
        department_name = data.get('department_name')
        if DepartmentMapper.update_department(department_num, department_name) is not None:
            return make_response('', 200)
        else:
            return jsonify({'error': '修改部门失败'}), 500
    except Exception as e:
        return jsonify({'error': '修改部门失败: ' + str(e)}), 500


@manageDepartment.route('/updatePosition', methods=['POST'])  # 删除职位
def update_position():
    try:
        data = request.get_json()
        position_num = data.get('num')
        position_name = data.get('position_name')
        if PositionMapper.update_position(position_num, position_name) is not None:
            return make_response('', 200)
        else:
            return jsonify({'error': '修改职位失败'}), 500
    except Exception as e:
        return jsonify({'error': '修改职位失败: ' + str(e)}), 500
