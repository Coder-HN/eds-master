from models import TableDepartment, TableDepartmentPosition, TablePosition
from database import db
from mapper import PositionMapper


def add_department(department: TableDepartment):
    new_department = TableDepartment(department_name=department.department_name)
    db.session.add(new_department)
    db.session.commit()
    return new_department


def get_department_by_num(department_num):
    return TableDepartment.query.filter_by(num=department_num).first()


def get_department_by_name(department_name):
    return TableDepartment.query.filter_by(department_name=department_name).first()


def get_all_departments():
    return TableDepartment.query.all()


# 修改部门信息
def update_department(department_num, department_name_new):
    department = TableDepartment.query.filter_by(num=department_num).first()
    if department:
        department.department_name = department_name_new
        db.session.commit()
        return department
    else:
        return None


# 删除部门
def delete_department(department_num):
    department = TableDepartment.query.filter_by(num=department_num).first()
    if department:
        db.session.delete(department)
        db.session.commit()
        return True  # 删除成功
    else:
        return False


def delete_department_complex(department_num):
    # 先删除关系、职位
    if not delete_department_position(TableDepartmentPosition(department_num=department_num)):
        return False
    # 再删除部门
    return delete_department(department_num)


# 删除部门职位关系
def delete_department_position(department_position: TableDepartmentPosition):
    position_num = department_position.position_num
    department_num = department_position.department_num
    department_position_list = []
    # 删除职位时
    if position_num is not None and department_num is not None:
        department_position_new = TableDepartmentPosition.query.filter_by(
            position_num=position_num,
            department_num=department_num
        ).first()
        department_position_list.append(department_position_new)  # 只有一个
    # 删除部门时
    if position_num is None and department_num is not None:
        department_position_list = TableDepartmentPosition.query.filter_by(
            department_num=department_num
        ).all()  # 可能有多个
    # 如果找到服务，执行删除关系操作
    if len(department_position_list) != 0:
        for dp in department_position_list:
            db.session.delete(dp)
        db.session.commit()
    # 删除部门时
    if position_num is None and department_num is not None:
        for department_position in department_position_list:
            if not PositionMapper.delete_position(department_position.position_num):
                return False
    return True


def get_position_by_department_num(department_num):
    list_department_position_nums = TableDepartmentPosition.query.filter_by(department_num=department_num).all()
    position_list = []
    for department_position_nums in list_department_position_nums:
        position_num = department_position_nums.position_num
        position = TablePosition.query.filter_by(num=position_num).first()
        position_list.append(position)
    return position_list


def get_department_by_position_num(position_num):
    position_department_num = TableDepartmentPosition.query.filter_by(position_num=position_num).first()
    return position_department_num.department_num
