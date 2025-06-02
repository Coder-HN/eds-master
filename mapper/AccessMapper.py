from sqlalchemy import desc
from models import TableAccess
from database import db
from mapper import UserMapper, ServiceMapper


def add_access(access: TableAccess):
    new_access = access
    db.session.add(new_access)
    db.session.commit()
    return new_access


def delete_access(access_num):
    access = TableAccess.query.filter_by(num=access_num).first()
    # 如果找到，执行删除操作
    if access:
        db.session.delete(access)
        db.session.commit()
        return True  # 删除成功
    else:
        return False  # 未找到


def get_access_by_num(access_num):
    return TableAccess.query.filter_by(num=access_num).first()


def get_all_access_count():
    count = db.session.query(TableAccess).count()
    return count


def get_all_access_paginated(offset, limit):
    query = db.session.query(
        TableAccess.num,
        TableAccess.user_num,
        TableAccess.service_num,
        TableAccess.access_flag,
        TableAccess.access_time,
        TableAccess.result
    ).order_by(desc(TableAccess.access_time)).offset(offset).limit(limit)
    results = query.all()
    return [dict(num=row[0], user_num=row[1], service_num=row[2], access_flag=row[3], access_time=row[4], result=row[5])
            for row in results]


def get_access_by_multiple_conditions_count(employee_id=None, name=None, service_name=None,
                                            start_time=None, end_time=None):
    query = TableAccess.query
    users = None
    service = None
    user_num = None
    service_num = None

    if employee_id or name:
        users = UserMapper.get_users_by_multiple_conditions(employee_id=employee_id, name=name)
        if len(users) == 0:
            user_num = -1
    if service_name:
        service = ServiceMapper.get_service_by_name(service_name)

    if users is not None and len(users) != 0:
        user_num = users[0].num
    if service:
        service_num = service.num

    if user_num is not None:
        query = query.filter(TableAccess.user_num == user_num)
    if service_num is not None:
        query = query.filter(TableAccess.service_num == service_num)
    if start_time:
        query = query.filter(TableAccess.access_time >= start_time)
    if end_time:
        query = query.filter(TableAccess.access_time <= end_time)

    return query.count()


def get_access_by_multiple_conditions_paginated(offset=None, limit=None, employee_id=None, name=None, service_name=None,
                                                start_time=None, end_time=None):
    query = TableAccess.query
    users = None
    service = None
    user_num = None
    service_num = None
    # 处理用户筛选
    if employee_id or name:
        users = UserMapper.get_users_by_multiple_conditions(employee_id=employee_id, name=name)
        if len(users) == 0:
            # 设置一个无效 user_num 来确保查询为空
            user_num = -1
    if service_name:
        service = ServiceMapper.get_service_by_name(service_name)

    if users is not None and len(users) != 0:
        user_num = users[0].num
    if service:
        service_num = service.num

    # 添加过滤条件
    if user_num is not None:
        query = query.filter(TableAccess.user_num == user_num)
    if service_num is not None:
        query = query.filter(TableAccess.service_num == service_num)
    if start_time:
        query = query.filter(TableAccess.access_time >= start_time)
    if end_time:
        query = query.filter(TableAccess.access_time <= end_time)

    # 分页 + 排序
    query = query.order_by(desc(TableAccess.access_time))
    if limit is not None:
        query = query.offset(offset).limit(limit)
    results = query.all()
    return [
        {
            "num": row.num,
            "user_num": row.user_num,
            "service_num": row.service_num,
            "access_flag": row.access_flag,
            "access_time": row.access_time,
            "result": row.result,
            "value_hand_left": row.value_hand_left,
            "value_hand_right": row.value_hand_right,
            "value_foot_left": row.value_foot_left,
            "value_foot_right": row.value_foot_right,
            "unregist": row.unregist,
            "will_fail": row.will_fail,
            "result_hand_left": row.result_hand_left,
            "result_hand_right": row.result_hand_right,
            "result_foot_left": row.result_foot_left,
            "result_foot_right": row.result_foot_right
        }
        for row in results
    ]


# 获取出去记录的上一次进的记录
def get_access_enter_by_leave(user_num):
    query = TableAccess.query
    query = query.filter(
        (TableAccess.user_num == user_num) &
        (TableAccess.access_flag == 1) &
        (TableAccess.result == 1)
    )  # 只要成功进门的
    # 获取最近一次进的记录
    second_record = query.order_by(desc(TableAccess.num)).offset(1).limit(1).first()
    # 处理结果
    return second_record
