from decimal import Decimal
from sqlalchemy import desc

from mapper import UserMapper
from models import TableAttend
from database import db


def get_attend_by_num(attend_num):
    return TableAttend.query.filter_by(num=attend_num).first()


def get_all_attend():
    query = db.session.query(TableAttend.num,
                             TableAttend.user_num,
                             TableAttend.attend_date,
                             TableAttend.attend_time,
                             TableAttend.attend_time_require,
                             TableAttend.access_times,
                             TableAttend.access_times_limit
                             )
    results = query.order_by(desc(TableAttend.attend_date)).all()
    return [dict(num=row[0], user_num=row[1], attend_date=row[2], attend_time=row[3],
                 attend_time_require=row[4], access_times=row[5], access_times_limit=row[6])
            for row in results]


def get_attend_by_user_num_attend_date(user_num, attend_date):
    return TableAttend.query.filter_by(user_num=user_num, attend_date=attend_date).first()


def update_attend(attend_num, hours_difference):
    attend = TableAttend.query.filter_by(num=attend_num).first()
    attend.attend_time = attend.attend_time + Decimal(hours_difference)
    attend.access_times = attend.access_times + 1
    db.session.commit()
    return attend


def add_attend(attend: TableAttend):
    new_attend = attend
    db.session.add(new_attend)
    db.session.commit()
    return new_attend


def get_attend_by_multiple_conditions(employee_id=None, card_id=None, name=None, department_num=None,
                                      start_time=None, end_time=None):
    users = []
    user_num = None
    if employee_id is not None or card_id is not None or name is not None or department_num is not None:
        users = UserMapper.get_users_by_multiple_conditions(employee_id=employee_id, card_id=card_id, name=name,
                                                            department_num=department_num)
    if len(users) == 1:
        user_num = users[0].num
    query = TableAttend.query
    if user_num:
        query = query.filter(TableAttend.user_num == user_num)
    if start_time:
        query = query.filter(TableAttend.attend_date >= start_time)
    if end_time:
        query = query.filter(TableAttend.attend_date <= end_time)
    return query.order_by(desc(TableAttend.attend_date)).all()
