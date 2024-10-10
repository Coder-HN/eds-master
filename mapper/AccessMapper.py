from sqlalchemy import desc

from models import TableAccess
from database import db
from mapper import UserMapper, ServiceMapper


def add_access(access: TableAccess):
    new_access = access
    db.session.add(new_access)
    db.session.commit()
    return new_access


def get_access_by_num(access_num):
    return TableAccess.query.filter_by(num=access_num).first()


def get_all_access():
    # TableAccess.query
    query = db.session.query(TableAccess.num,
                             TableAccess.user_num,
                             TableAccess.service_num,
                             TableAccess.access_flag,
                             TableAccess.access_time,
                             TableAccess.result
                             )
    results = query.order_by(desc(TableAccess.access_time)).all()
    return [dict(num=row[0], user_num=row[1], service_num=row[2], access_flag=row[3], access_time=row[4], result=row[5])
            for row in results]


def get_access_by_multiple_conditions(employee_id=None, name=None, service_name=None,
                                      start_time=None, end_time=None):
    users = []
    service = None
    user_num = None
    service_num = None
    if employee_id or name:
        users = UserMapper.get_users_by_multiple_conditions(employee_id=employee_id, name=name)
    if service_name:
        service = ServiceMapper.get_service_by_name(service_name)
    if len(users) == 1:
        user_num = users[0].num
    if service:
        service_num = service.num
    query = TableAccess.query
    if user_num:
        query = query.filter(TableAccess.user_num == user_num)
    if service_num:
        query = query.filter(TableAccess.service_num == service_num)
    if start_time:
        query = query.filter(TableAccess.access_time >= start_time)
    if end_time:
        query = query.filter(TableAccess.access_time <= end_time)
    return query.order_by(desc(TableAccess.access_time)).all()


# 获取出去记录的上一次进的记录
def get_access_enter_by_leave(user_num):
    query = TableAccess.query
    query = query.filter(TableAccess.user_num == user_num)
    # 获取最近一次进的记录
    second_record = query.order_by(desc(TableAccess.num)).offset(1).limit(1).first()
    # 处理结果
    return second_record
