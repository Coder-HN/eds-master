from flask import Blueprint, request, jsonify, make_response, current_app

from mapper import ServiceMapper
from models import TableService

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
    except Exception:
        return jsonify({'error': '获取所有设备失败'}), 500
    response = {
        "data": services_list
    }
    return jsonify(response), 200


@manageService.route('/searchService', methods=['POST'])  # 搜索设备
def search_services():
    service_id = request.form.get('service_id')
    service_name = request.form.get('service_name')
    try:
        all_services = ServiceMapper.get_services_by_multiple_conditions(service_id, service_name)
        services_list = [service.to_dict() for service in all_services]
    except Exception:
        return jsonify({'error': '搜索设备失败'}), 500
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
    if ServiceMapper.add_service(new_service):
        return make_response('', 200)
    else:
        return jsonify({'error': '添加数据失败'}), 500


@manageService.route('/getRStandard', methods=['POST'])  # 添加设备
def get_r_standard():
    new_service = TableService()
    # 处理其他数据
    new_service.service_id = request.form.get('service_id')
    new_service.service_name = request.form.get('service_name')
    if ServiceMapper.add_service(new_service):
        return make_response('', 200)
    else:
        return jsonify({'error': '添加数据失败'}), 500
