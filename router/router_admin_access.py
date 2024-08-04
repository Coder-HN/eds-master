import datetime
import os

from flask import Blueprint, request, jsonify, send_file

from config import Config
from mapper import UserMapper, ServiceMapper, AccessMapper
from utils import timeHelper
from utils.dbHelper import export_mysql_to_sql

"""
进出记录查询
/admin/searchAccess：查询进出记录，按照 姓名，工号，部门进行数据查询，包括进出时间，进出记录
"""

searchAccess = Blueprint('searchAccess', __name__, url_prefix='/api/admin/searchAccess')


@searchAccess.route('/getAllAccess', methods=['GET'])  # 获取所有进出记录
def get_all_access():
    try:
        access_list = AccessMapper.get_all_access()
        for access in access_list:
            access_time = access['access_time'].strftime('%Y-%m-%d %H:%M:%S')
            access['access_time'] = access_time
            user_num = access.get("user_num")
            user = UserMapper.get_user_by_num(user_num)
            access["name"] = user.name
            access["employee_id"] = user.employee_id
            access["department"] = user.department
            service_num = access.get("service_num")
            service = ServiceMapper.get_service_by_num(service_num)
            access["service_id"] = service.service_id
            access["service_name"] = service.service_name
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": access_list
    }
    return jsonify(response), 200


@searchAccess.route('/getDetailAccess', methods=['Post'])  # 获取进出记录的详细信息
def get_detail_access():
    num = request.form.get('num')
    try:
        access = AccessMapper.get_access_by_num(num)
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": access.to_dict()
    }
    return jsonify(response), 200


@searchAccess.route('/search', methods=['POST'])  # 搜索进出记录
def search():
    start_time = None
    end_time = None
    employee_id = request.form.get('employee_id')
    name = request.form.get('name')
    department = request.form.get('department')
    service_name = request.form.get('service_name')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    if start_time_str:
        start_time = timeHelper.parse_datetime(start_time_str)
        start_time = timeHelper.get_start_of_day(start_time)
    if end_time_str:
        end_time = timeHelper.parse_datetime(end_time_str)
        end_time = timeHelper.get_end_of_day(end_time)
    try:
        all_access = AccessMapper.get_access_by_multiple_conditions(employee_id, name, department, service_name,
                                                                    start_time, end_time)
        access_list = [access.to_dict() for access in all_access]
        for access in access_list:
            access_time = access['access_time'].strftime('%Y-%m-%d %H:%M:%S')
            access['access_time'] = access_time
            user_num = access.get("user_num")
            user = UserMapper.get_user_by_num(user_num)
            access["name"] = user.name
            access["employee_id"] = user.employee_id
            access["department"] = user.department
            service_num = access.get("service_num")
            service = ServiceMapper.get_service_by_num(service_num)
            access["service_id"] = service.service_id
            access["service_name"] = service.service_name
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": access_list
    }
    return jsonify(response), 200


# 定义导出路由
@searchAccess.route('/download_db', methods=['GET'])
def upload_db():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"edsystem_{timestamp}.sql"
    output_file = os.path.join(Config.SQL_DATA, file_name)
    if export_mysql_to_sql(output_file):
        response = send_file(output_file, as_attachment=True, download_name=file_name)
        return response, 200
    else:
        return jsonify({"error": "导出数据库失败"}), 500

# # 定义导入路由
# @searchAccess.route('/upload_db', methods=['POST'])
# def upload_db():
#     timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#     output_file = f"backup_{timestamp}.sql"
#     if export_mysql_to_sql(mysql_config, output_file):
#         return send_file(output_file, as_attachment=True, download_name=output_file)
#     else:
#         return jsonify({"error": "Failed to export database"}), 500
