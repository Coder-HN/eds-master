from models import TableUser
from database import db


def is_exist(employee_id, card_id):
    res = False
    msg = []
    list_user_num = []
    user = TableUser.query.filter_by(employee_id=employee_id).first()
    if user is not None:
        res = True
        st = "已离职" if user.is_delete == 1 else "未离职;"
        msg.append(f"employee_id={employee_id}员工已存在,name={user.name},{st}")
        list_user_num.append(user.num)
    user1 = TableUser.query.filter_by(card_id=card_id).first()
    if user1 is not None:
        res = True
        st = "已离职" if user1.is_delete == 1 else "未离职;"
        msg.append(f"card_id={card_id}员工已存在,name={user1.name},{st}")
        list_user_num.append(user1.num)
    return res, msg, list_user_num


def add_user(user: TableUser):
    # 判断 user.is_delete，如果为 None 则设置为 0，否则使用 user.is_delete 的值
    is_delete_value = 0 if user.is_delete is None else user.is_delete

    new_user = TableUser(
        employee_id=user.employee_id,
        name=user.name,
        position_num=user.position_num,
        department_num=user.department_num,
        card_id=user.card_id,
        pic_path=user.pic_path,
        is_delete=is_delete_value  # 动态设置 is_delete 的值
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user


def get_user_by_num(user_num):
    return TableUser.query.filter_by(num=user_num).first()


def get_user_by_card_id(card_id):
    return TableUser.query.filter_by(card_id=card_id).first()


# 获取未离职人员列表
def get_all_users():
    return TableUser.query.filter(TableUser.is_delete == 0).order_by(TableUser.num.desc()).all()


def get_all_users_excel():
    return TableUser.query.all()


# 获取离职人员列表
def get_all_users_deleted():
    return TableUser.query.filter(TableUser.is_delete == 1).all()


# 多条件查询
def get_users_by_multiple_conditions(request_type='1', employee_id=None, card_id=None, name=None, department_num=None,
                                     position_num=None):
    query = TableUser.query
    if request_type == '1':
        query = query.filter(TableUser.is_delete == 0)
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
    if updated_user.employee_id is not None:
        user.employee_id = updated_user.employee_id
        is_change = True
    if updated_user.name is not None:
        user.name = updated_user.name
        is_change = True
    if updated_user.department_num is not None:
        user.department_num = updated_user.department_num
        is_change = True
    if updated_user.position_num is not None:
        user.position_num = updated_user.position_num
        is_change = True
    if updated_user.card_id is not None:
        user.card_id = updated_user.card_id
        is_change = True
    if updated_user.pic_path is not None:
        user.pic_path = updated_user.pic_path
        is_change = True
    if updated_user.is_delete is not None:
        user.is_delete = updated_user.is_delete
        is_change = True
    db.session.commit()
    if is_change:
        return True
    else:
        return False
