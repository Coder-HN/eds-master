from models import TableService
from database import db


def add_service(service: TableService):
    new_service = TableService(service_id=service.service_id,
                               service_name=service.service_name, )
    db.session.add(new_service)
    db.session.commit()
    return new_service


def get_service_by_num(service_num):
    return TableService.query.filter_by(num=service_num).first()


def get_all_services():
    return TableService.query.all()


# 多条件查询
def get_services_by_multiple_conditions(service_id=None, service_name=None):
    query = TableService.query
    if service_id:
        query = query.filter(TableService.service_id == service_id)
    if service_name:
        query = query.filter(TableService.service_name == service_name)
    return query.all()


def get_service_by_id(service_id):
    service = TableService.query.filter_by(service_id=service_id).first()
    return service


# 修改设备信息
def update_service(service_num, updated_service: TableService):
    service = TableService.query.filter_by(num=service_num).first()
    if service:
        service.service_id = updated_service.service_id
        service.service_name = updated_service.service_name
        db.session.commit()
        return service
    else:
        return None


# 删除设备
def delete_service(service_num):
    service = TableService.query.filter_by(num=service_num).first()
    # 如果找到服务，执行删除操作
    if service:
        db.session.delete(service)
        db.session.commit()
        return True  # 删除成功
    else:
        return False  # 服务未找到
