from mapper import DepartmentMapper
from models import TablePosition, TableDepartmentPosition
from database import db


def add_position(position_name):
    new_position = TablePosition(position_name=position_name)
    db.session.add(new_position)
    db.session.commit()
    return new_position


def add_position_department(position_num, department_num):
    new_position_department = TableDepartmentPosition(position_num=position_num, department_num=department_num)
    db.session.add(new_position_department)
    db.session.commit()
    return new_position_department


def get_position_by_num(position_num):
    return TablePosition.query.filter_by(num=position_num).first()


def get_position_by_name(position_name):
    return TablePosition.query.filter_by(position_name=position_name).first()


def get_all_positions():
    return TablePosition.query.all()


# 修改职位信息
def update_position(position_num, position_name_new):
    position = TablePosition.query.filter_by(num=position_num).first()
    if position:
        position.position_name = position_name_new
        db.session.commit()
        return position
    else:
        return None


# 删除职位
def delete_position(position_num):
    position = TablePosition.query.filter_by(num=position_num).first()
    if position:
        db.session.delete(position)
        db.session.commit()
        return True  # 删除成功
    else:
        return False


def delete_position_complex(position_num, department_num):
    # 先删除关系
    if not DepartmentMapper.delete_department_position(
            TableDepartmentPosition(department_num=department_num, position_num=position_num)):
        return False
    # 如果关系中全部都不存在改职位再删除职位
    department_num_list = DepartmentMapper.get_department_by_position_num(position_num)
    if len(department_num_list) == 0:
        return delete_position(position_num)
    return True
