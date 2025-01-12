import datetime
from io import BytesIO
import pandas as pd
from flask import Blueprint, request, jsonify, send_file, make_response, current_app
from mapper import UserMapper, ServiceMapper, AccessMapper, DepartmentMapper, RStandardMapper
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
        # 获取分页参数
        page = int(request.args.get('page', 1))  # 当前页码，默认为第 1 页
        page_size = int(request.args.get('pageSize', 5))  # 每页记录数，默认为 5 条
        # 计算分页的起始索引和结束索引
        offset = (page - 1) * page_size
        limit = page_size
        # 查询所有进出记录 access_list = AccessMapper.get_all_access()
        total_records = AccessMapper.get_all_access_count()  # 获取总记录数
        access_list = AccessMapper.get_all_access_paginated(offset, limit)  # 获取分页后的记录
        for access in access_list:
            access_time = access['access_time'].strftime('%Y-%m-%d %H:%M:%S')
            access['access_time'] = access_time
            user_num = access.get("user_num")
            user = UserMapper.get_user_by_num(user_num)
            access["name"] = user.name
            access["employee_id"] = user.employee_id
            department = DepartmentMapper.get_department_by_num(user.department_num)
            access["department"] = department.department_name
            service_num = access.get("service_num")
            service = ServiceMapper.get_service_by_num(service_num)
            access["service_id"] = service.service_id
            access["service_name"] = service.service_name
        # 构造响应数据
        response = {
            "data": access_list,
            "pagination": {
                "current": page,
                "pageSize": page_size,
                "total": total_records,
            }
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@searchAccess.route('/getDetailAccess', methods=['Post'])  # 获取进出记录的详细信息
def get_detail_access():
    num = request.form.get('num')
    try:
        access = AccessMapper.get_access_by_num(num)
        service = ServiceMapper.get_service_by_num(access.service_num)
        r_standard = RStandardMapper.get_r_standard_by_num(service.r_standard_num)
        data = access.to_dict()
        data['hand_left_min'] = r_standard.hand_left_min
        data['hand_left_max'] = r_standard.hand_left_max
        data['hand_right_min'] = r_standard.hand_right_min
        data['hand_right_max'] = r_standard.hand_right_max
        data['foot_left_min'] = r_standard.foot_left_min
        data['foot_left_max'] = r_standard.foot_left_max
        data['foot_right_min'] = r_standard.foot_right_min
        data['foot_right_max'] = r_standard.foot_right_max
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": data
    }
    return jsonify(response), 200


@searchAccess.route('/deleteAccess', methods=['POST'])  # 删除进出记录
def delete_access():
    data = request.get_json()
    num = data.get('num')
    is_change = AccessMapper.delete_access(num)
    if is_change:
        return make_response('', 200)
    else:
        return jsonify({'error': '删除进出记录失败'}), 500


@searchAccess.route('/search', methods=['POST'])  # 搜索进出记录
def search():
    try:
        start_time = None
        end_time = None
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        service_name = request.form.get('service_name')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        if start_time_str:
            start_time = timeHelper.parse_datetime(start_time_str)
            start_time = timeHelper.get_start_of_day(start_time)
        if end_time_str:
            end_time = timeHelper.parse_datetime(end_time_str)
            end_time = timeHelper.get_end_of_day(end_time)
        all_access = AccessMapper.get_access_by_multiple_conditions(employee_id, name, service_name,
                                                                    start_time, end_time)
        access_list = [access.to_dict() for access in all_access]
        for access in access_list:
            access_time = access['access_time'].strftime('%Y-%m-%d %H:%M:%S')
            access['access_time'] = access_time
            user_num = access.get("user_num")
            user = UserMapper.get_user_by_num(user_num)
            access["name"] = user.name
            access["employee_id"] = user.employee_id
            department = DepartmentMapper.get_department_by_num(user.department_num)
            access["department"] = department.department_name
            service_num = access.get("service_num")
            service = ServiceMapper.get_service_by_num(service_num)
            access["service_id"] = service.service_id
            access["service_name"] = service.service_name

            r_standard = RStandardMapper.get_r_standard_by_num(service.r_standard_num)
            access['hand_left_min'] = r_standard.hand_left_min
            access['hand_left_max'] = r_standard.hand_left_max
            access['hand_right_min'] = r_standard.hand_right_min
            access['hand_right_max'] = r_standard.hand_right_max
            access['foot_left_min'] = r_standard.foot_left_min
            access['foot_left_max'] = r_standard.foot_left_max
            access['foot_right_min'] = r_standard.foot_right_min
            access['foot_right_max'] = r_standard.foot_right_max
    except Exception as e:
        return jsonify({'error': e}), 500
    response = {
        "data": access_list
    }
    return jsonify(response), 200


# 定义导出路由
@searchAccess.route('/download_db', methods=['GET'])
def download_db():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"edsystem_{timestamp}.sql"

    output = export_mysql_to_sql()
    if output:
        # 返回生成的 SQL 文件作为下载
        return send_file(
            output,
            as_attachment=True,
            download_name=file_name,
            mimetype='application/sql'
        )
    else:
        return jsonify({"error": "导出数据库失败"}), 500


# 定义导出路由
@searchAccess.route('/download_excel', methods=['POST'])
def download_excel():
    try:
        start_time = None
        end_time = None
        employee_id = request.form.get('employee_id')
        name = request.form.get('name')
        service_name = request.form.get('service_name')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        if start_time_str:
            start_time = timeHelper.parse_datetime(start_time_str)
            start_time = timeHelper.get_start_of_day(start_time)
        if end_time_str:
            end_time = timeHelper.parse_datetime(end_time_str)
            end_time = timeHelper.get_end_of_day(end_time)
        all_access = AccessMapper.get_access_by_multiple_conditions(employee_id, name, service_name,
                                                                    start_time, end_time)
        access_list = [access.to_dict() for access in all_access]
        for access in access_list:
            access_time = access['access_time'].strftime('%Y-%m-%d %H:%M:%S')
            access['access_time'] = access_time
            user_num = access.get("user_num")
            user = UserMapper.get_user_by_num(user_num)
            access["name"] = user.name
            access["employee_id"] = user.employee_id
            department = DepartmentMapper.get_department_by_num(user.department_num)
            access["department"] = department.department_name
            service_num = access.get("service_num")
            service = ServiceMapper.get_service_by_num(service_num)
            access["service_id"] = service.service_id
            access["service_name"] = service.service_name
            r_standard = RStandardMapper.get_r_standard_by_num(service.r_standard_num)
            access['hand_left_min'] = str(r_standard.hand_left_min) + "KΩ"
            access['hand_left_max'] = str(r_standard.hand_left_max) + "KΩ"
            access['hand_right_min'] = str(r_standard.hand_right_min) + "KΩ"
            access['hand_right_max'] = str(r_standard.hand_right_max) + "KΩ"
            access['foot_left_min'] = str(r_standard.foot_left_min) + "KΩ"
            access['foot_left_max'] = str(r_standard.foot_left_max) + "KΩ"
            access['foot_right_min'] = str(r_standard.foot_right_min) + "KΩ"
            access['foot_right_max'] = str(r_standard.foot_right_max) + "KΩ"

            if access['result'] == 1:
                access['result'] = "测试合格"
            elif access['result'] == 2:
                access['result'] = "测试不合格"

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

            if access["access_flag"] == 1:
                access["access_flag"] = "进门"
            elif access["access_flag"] == 2:
                access["access_flag"] = "出门"

            del access['num']
            del access['user_num']
            del access['service_num']
            del access['unregist']
            del access['will_fail']
            del access['result_hand_left']
            del access['result_hand_right']
            del access['result_foot_left']
            del access['result_foot_right']

        # 使用 pandas 将数据转换为 DataFrame
        df = pd.DataFrame(access_list)
        # 创建输出流，用于生成 Excel 文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # 将 DataFrame 写入 Excel 文件，保持与导入格式一致的列
            df.to_excel(writer, index=False, sheet_name='进出记录数据')
            # 获取 worksheet 对象
            worksheet = writer.sheets['进出记录数据']
            # 设置列宽仅根据列名长度
            for idx, col in enumerate(df.columns):  # 遍历 DataFrame 的每一列
                if col == 'access_time':
                    worksheet.set_column(idx, idx, len(col) * 2)
                else:
                    worksheet.set_column(idx, idx, len(col) + 2)  # 根据列名长度设置列宽，加 2 以增加空白
        output.seek(0)  # 将指针移到文件开头

        # 返回生成的 Excel 文件
        return send_file(output,
                         download_name='进出记录数据.xlsx',
                         as_attachment=True,
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        # 记录并返回错误信息
        current_app.logger.error(f"Error exporting user Excel: {str(e)}")
        return jsonify({'error': str(e)}), 500
