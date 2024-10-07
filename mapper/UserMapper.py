from models import TableUser
from database import db


def add_user(user: TableUser):
    new_user = TableUser(employee_id=user.employee_id,
                         name=user.name,
                         position_num=user.position_num,
                         department_num=user.department_num,
                         card_id=user.card_id,
                         pic_path=user.pic_path,
                         is_delete=0)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def get_user_by_num(user_num):
    return TableUser.query.filter_by(num=user_num).first()


def get_all_users():
    return TableUser.query.filter(TableUser.is_delete == 0).all()


# 多条件查询
def get_users_by_multiple_conditions(employee_id=None, card_id=None, name=None, department_num=None,
                                     position_num=None):
    query = TableUser.query
    if employee_id:
        query = query.filter(TableUser.employee_id == employee_id)
    if card_id:
        query = query.filter(TableUser.card_id == card_id)
    if name:
        query = query.filter(TableUser.name == name)
    if department_num:
        query = query.filter(TableUser.department_num == department_num)
    if position_num:
        query = query.filter(TableUser.position_num == position_num)
    return query.all()


def get_user_by_employee_id(employee_id):
    user = TableUser.query.filter_by(employee_id=employee_id).first()
    return user


# 修改员工信息or删除员工（将is_delete置为1）
def update_user(user_num, updated_user: TableUser):
    user = TableUser.query.filter_by(num=user_num).first()
    is_change = False
    if updated_user.employee_id:
        user.employee_id = updated_user.employee_id
        is_change = True
    if updated_user.name:
        user.name = updated_user.name
        is_change = True
    if updated_user.department_num:
        user.department_num = updated_user.department_num
        is_change = True
    if updated_user.position_num:
        user.position_num = updated_user.position_num
        is_change = True
    if updated_user.card_id:
        user.card_id = updated_user.card_id
        is_change = True
    if updated_user.pic_path:
        user.pic_path = updated_user.pic_path
        is_change = True
    if updated_user.is_delete:
        user.is_delete = updated_user.is_delete
        is_change = True
    db.session.commit()
    if is_change:
        return True
    else:
        return False
