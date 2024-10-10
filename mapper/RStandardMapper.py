from models import TableRStandard
from database import db


def add_r_standard(r_standard: TableRStandard):
    db.session.add(r_standard)
    db.session.commit()
    return r_standard.num


def get_r_standard_by_num(r_standard_num):
    return TableRStandard.query.filter_by(num=r_standard_num).first()


def get_r_standard_by_name(r_name):
    return TableRStandard.query.filter_by(r_name=r_name).first()


def get_all_r_standards():
    return TableRStandard.query.all()


# 修改
def update_r_standard(num, r_standard_new: TableRStandard):
    r_standard = TableRStandard.query.filter_by(num=num).first()
    if r_standard:
        r_standard.r_name = r_standard_new.r_name

        r_standard.hand_left_min = r_standard_new.hand_left_min
        r_standard.hand_left_max = r_standard_new.hand_left_max
        r_standard.hand_right_min = r_standard_new.hand_right_min
        r_standard.hand_right_max = r_standard_new.hand_right_max

        r_standard.foot_left_min = r_standard_new.foot_left_min
        r_standard.foot_left_max = r_standard_new.foot_left_max
        r_standard.foot_right_min = r_standard_new.foot_right_min
        r_standard.foot_right_max = r_standard_new.foot_right_max

        db.session.commit()
        return r_standard
    else:
        return None


# 删除职位
def delete_r_standard(r_standard_num):
    r_standard = TableRStandard.query.filter_by(num=r_standard_num).first()
    if r_standard:
        db.session.delete(r_standard)
        db.session.commit()
        return True  # 删除成功
    else:
        return False
