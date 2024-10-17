from flask import Blueprint, jsonify, request, current_app

from mapper import AttendMapper, UserMapper, DepartmentMapper, PositionMapper
from utils import timeHelper

"""
员工考勤查询
/admin/searchAttend：查询日常考勤
"""

searchAttend = Blueprint('searchAttend', __name__, url_prefix='/api/admin/searchAttend')


@searchAttend.route('/getAllAttend', methods=['GET'])  # 获取所有出勤记录
def get_all_attend():
    try:
        attend_list = AttendMapper.get_all_attend()
        for attend in attend_list:
            attend_date = attend['attend_date'].strftime('%Y-%m-%d')
            attend['attend_date'] = attend_date
            user_num = attend["user_num"]
            user = UserMapper.get_user_by_num(user_num)
            attend["employee_id"] = user.employee_id
            attend["card_id"] = user.card_id
            attend["name"] = user.name
            department_name = None
            if user.department_num is not None:
                department = DepartmentMapper.get_department_by_num(user.department_num)
                department_name = department.department_name
            attend["department"] = department_name
            position_name = None
            if user.position_num is not None:
                position = PositionMapper.get_position_by_num(user.position_num)
                position_name = position.position_name
            attend["position"] = position_name
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": attend_list
    }
    return jsonify(response), 200


@searchAttend.route('/search', methods=['POST'])  # 搜索出勤记录
def search():
    start_time = None
    end_time = None
    employee_id = request.form.get('employee_id')
    card_id = request.form.get('card_id')
    name = request.form.get('name')
    department_name = request.form.get('department')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    if start_time_str:
        start_time = timeHelper.parse_datetime(start_time_str)
        start_time = timeHelper.get_start_of_day(start_time)
    if end_time_str:
        end_time = timeHelper.parse_datetime(end_time_str)
        end_time = timeHelper.get_end_of_day(end_time)
    try:
        department_num = None
        if department_name is not None:
            department = DepartmentMapper.get_department_by_name(department_name)
            department_num = department.num
        all_attend = AttendMapper.get_attend_by_multiple_conditions(employee_id, card_id, name, department_num,
                                                                    start_time, end_time)
        attend_list = [attend.to_dict() for attend in all_attend]
        for attend in attend_list:
            user_num = attend.get("user_num")
            user = UserMapper.get_user_by_num(user_num)
            attend_date = attend['attend_date'].strftime('%Y-%m-%d')
            attend['attend_date'] = attend_date
            attend["employee_id"] = user.employee_id
            attend["card_id"] = user.card_id
            attend["name"] = user.name
            department_name = None
            if user.department_num is not None:
                department = DepartmentMapper.get_department_by_num(user.department_num)
                department_name = department.department_name
            attend["department"] = department_name
            position_name = None
            if user.position_num is not None:
                position = PositionMapper.get_position_by_num(user.position_num)
                position_name = position.position_name
            attend["position"] = position_name
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": attend_list
    }
    return jsonify(response), 200
