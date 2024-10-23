from flask import Blueprint, request, jsonify, make_response, current_app

from mapper import ServiceMapper, RStandardMapper
from models import TableService, TableRStandard

"""
设备管理
/admin/manageService：上传设备信息；设置设备名称，上岗时间，进出预警时间；静电检测板的标定
"""
manageService = Blueprint('manageService', __name__, url_prefix='/api/admin/manageService')


@manageService.route('/getAllServices', methods=['GET'])  # 获取所有设备
def get_all_services():
    try:
        all_services = ServiceMapper.get_all_services()
        services_list = [service.to_dict() for service in all_services]
        for service in services_list:
            r_standard = RStandardMapper.get_r_standard_by_num(int(service['r_standard_num']))
            service['r_name'] = r_standard.r_name
    except Exception as e:
        return jsonify({'error': '获取所有设备失败,error:' + str(e)}), 500
    response = {
        "data": services_list
    }
    return jsonify(response), 200


@manageService.route('/searchService', methods=['POST'])  # 搜索设备
def search_services():
    service_id = request.form.get('service_id')
    service_name = request.form.get('service_name')
    try:
        all_services = [ServiceMapper.get_service_by_id(service_id), ServiceMapper.get_service_by_name(service_name)]
        services_list = [service.to_dict() for service in all_services]
        for service in services_list:
            r_standard = RStandardMapper.get_r_standard_by_num(int(service['r_standard_num']))
            service['r_name'] = r_standard.r_name
    except Exception as e:
        return jsonify({'error': '搜索设备失败' + str(e)}), 500
    response = {
        "data": services_list
    }
    return jsonify(response), 200


@manageService.route('/deleteService', methods=['POST'])  # 删除设备
def delete_service():
    data = request.get_json()
    num = data.get('num')
    is_change = ServiceMapper.delete_service(num)
    if is_change:
        return make_response('', 200)
    else:
        return jsonify({'error': '删除设备失败'}), 500


@manageService.route('/addService', methods=['POST'])  # 添加设备
def add_service():
    new_service = TableService()
    # 处理其他数据
    new_service.service_id = request.form.get('service_id')
    new_service.service_name = request.form.get('service_name')
    new_service.r_standard_num = request.form.get('r_num')
    if ServiceMapper.add_service(new_service):
        return make_response('', 200)
    else:
        return jsonify({'error': '添加数据失败'}), 500


@manageService.route('/updateService', methods=['POST'])  # 修改设备
def update_service():
    data = request.get_json()
    new_service = TableService()
    # 处理其他数据
    num = data.get('num')
    new_service.service_id = data.get('service_id')
    new_service.service_name = data.get('service_name')
    r_name = data.get('r_name')
    r_standard = RStandardMapper.get_r_standard_by_name(r_name)
    new_service.r_standard_num = r_standard.num
    if ServiceMapper.update_service(num, new_service):
        return make_response('', 200)
    else:
        return jsonify({'error': '更新设备数据失败'}), 500


@manageService.route('/updateServiceTestPart', methods=['POST'])  # 修改设备
def update_service_test_part():
    data = request.get_json()
    num = data.get('num')
    new_test_part = data.get('test_part')
    if ServiceMapper.update_service_test_part(num, new_test_part):
        return make_response('', 200)
    else:
        return jsonify({'error': '更新设备数据失败'}), 500


@manageService.route('/getAllRStandard', methods=['GET'])  # 获取所有电阻标准
def get_all_r_standard():
    try:
        r_standard_list = RStandardMapper.get_all_r_standards()
        r_standard_list_dict = [r_standard.to_dict() for r_standard in r_standard_list]
    except Exception as e:
        return jsonify({'error': '获取所有电阻标准失败' + str(e)}), 500
    response = {
        "data": r_standard_list_dict
    }
    return jsonify(response), 200


@manageService.route('/addRStandard', methods=['POST'])  # 添加电阻标准
def add_r_standard():
    new_r_standard = TableRStandard()
    # 处理数据
    new_r_standard.r_name = request.form.get('r_name')
    new_r_standard.hand_left_min = float(request.form.get('hand_left_min'))
    new_r_standard.hand_left_max = float(request.form.get('hand_left_max'))
    new_r_standard.hand_right_min = float(request.form.get('hand_right_min'))
    new_r_standard.hand_right_max = float(request.form.get('hand_right_max'))
    new_r_standard.foot_left_min = float(request.form.get('foot_left_min'))
    new_r_standard.foot_left_max = float(request.form.get('foot_left_max'))
    new_r_standard.foot_right_min = float(request.form.get('foot_right_min'))
    new_r_standard.foot_right_max = float(request.form.get('foot_right_max'))
    num = RStandardMapper.add_r_standard(new_r_standard)
    if num:
        return jsonify({'num': num}), 200
    else:
        return jsonify({'error': '添加电阻标准数据失败'}), 500


@manageService.route('/updateRStandard', methods=['POST'])  # 更新电阻标准
def update_r_standard():
    data = request.get_json()
    new_r_standard = TableRStandard()
    # 处理数据
    num = int(data.get('num'))
    new_r_standard.r_name = data.get('r_name')
    new_r_standard.hand_left_min = float(data.get('hand_left_min'))
    new_r_standard.hand_left_max = float(data.get('hand_left_max'))
    new_r_standard.hand_right_min = float(data.get('hand_right_min'))
    new_r_standard.hand_right_max = float(data.get('hand_right_max'))
    new_r_standard.foot_left_min = float(data.get('foot_left_min'))
    new_r_standard.foot_left_max = float(data.get('foot_left_max'))
    new_r_standard.foot_right_min = float(data.get('foot_right_min'))
    new_r_standard.foot_right_max = float(data.get('foot_right_max'))
    if RStandardMapper.update_r_standard(num, new_r_standard):
        return make_response('', 200)
    else:
        return jsonify({'error': '更新电阻标准数据失败'}), 500


@manageService.route('/deleteRStandard', methods=['POST'])  # 删除设备
def delete_r_standard():
    data = request.get_json()
    num = data.get('num')
    is_change = RStandardMapper.delete_r_standard(num)
    if is_change:
        return make_response('', 200)
    else:
        return jsonify({'error': '删除电阻标准失败'}), 500
