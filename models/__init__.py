# 数据库数据表类定义
from sqlalchemy import ForeignKey, MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.schema import FetchedValue
from sqlalchemy.sql.schema import Column, Table
from sqlalchemy.sql.sqltypes import BigInteger, Date, DateTime, Integer, Numeric, String

from database import db

# 创建一个 MetaData 实例
metadata = MetaData()


# 生成models方法 sqlacodegen mysql+pymysql://root:root@localhost/edsystem > models.py
class TableUser(db.Model):
    __tablename__ = 'table_user'

    num = Column(BigInteger, primary_key=True, info='人员序号、主键')
    employee_id = Column(String(50, 'utf8mb4_0900_ai_ci'), info='工号', unique=True)
    card_id = Column(String(50, 'utf8mb4_0900_ai_ci'), info='卡号', unique=True)
    name = Column(String(50, 'utf8mb4_0900_ai_ci'), nullable=False, info='姓名')
    position_num = Column(ForeignKey('table_position.num', ondelete='SET NULL', onupdate='SET NULL'), index=True,
                          info='职位序号、外键')
    department_num = Column(ForeignKey('table_department.num', ondelete='SET NULL', onupdate='SET NULL'), index=True,
                            info='部门序号、外键')

    pic_path = Column(String(100, 'utf8mb4_0900_ai_ci'), info='照片,设置成路径，以 工号_卡号 命名')
    is_delete = Column(Integer, nullable=False, server_default=FetchedValue(), info='0表示未离职，1表示已离职')

    table_position = relationship('TablePosition', primaryjoin='TableUser.position_num == TablePosition.num',
                                  backref='table_user')
    table_department = relationship('TableDepartment', primaryjoin='TableUser.department_num == TableDepartment.num',
                                    backref='table_user')

    def __repr__(self):
        return f'<table_user {self.name}>'

    def to_dict(self):
        return {
            'num': self.num,
            'employee_id': self.employee_id,
            'name': self.name,
            'position_num': self.position_num,
            'department_num': self.department_num,
            'card_id': self.card_id,
            'pic_path': self.pic_path,
            'is_delete': self.is_delete
        }


class TableAccess(db.Model):
    __tablename__ = 'table_access'

    num = Column(BigInteger, primary_key=True, info='记录序号num\n,主键')
    user_num = Column(ForeignKey('table_user.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True,
                      info='人员序号num\n,外键')
    service_num = Column(ForeignKey('table_service.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                         index=True, info='设备序号num\n,外键')
    access_flag = Column(Integer, nullable=False, info='进出标志位，1或2，1表示进，2表示出')
    access_time = Column(DateTime, nullable=False, info='进出时间accessTime')
    result = Column(Integer, info='员工静电测试总结果，1"合格"2"不合格"3"免测"4"未测"5"禁测"')
    unregist = Column(Integer, info='表示员工刷卡时（特殊的临时卡），是否已登记，未登记值为1，登记值为2')
    will_fail = Column(String(10, 'utf8mb4_0900_ai_ci'),
                       info='标示员工的手环、静电鞋是否即将失效。 如000表示没有失效的\n第1位表示手环是否失效，0表示没有即将失效，1表示即将失效\n第2位表示左脚静电鞋是否失效，0表示没有即将失效，1表示即将失效\n第3位表示右脚静电鞋是否失效，0表示没有即将失效，1表示即将失效')
    result_hand_left = Column(Integer, info='左手测试结果，1"合格"2"不合格"3"免测"4"未测"5"禁测"')
    value_hand_left = Column(Numeric(10, 2), info='左手测试实际阻值,单位:兆欧姆')
    result_hand_right = Column(Integer, info='右手测试结果，"合格""不合格""免测""未测""禁测"')
    value_hand_right = Column(Numeric(10, 2), info='右手测试实际阻值,单位:兆欧姆')
    result_foot_left = Column(Integer, info='左脚测试结果，"合格""不合格""免测""未测""禁测"')
    value_foot_left = Column(Numeric(10, 2), info='左脚测试实际阻值,单位:兆欧姆')
    result_foot_right = Column(Integer, info='右脚测试结果，"合格""不合格""免测""未测""禁测"')
    value_foot_right = Column(Numeric(10, 2), info='右脚测试实际阻值,单位:兆欧姆')
    table_service = relationship('TableService', primaryjoin='TableAccess.service_num == TableService.num',
                                 backref='table_access')
    table_user = relationship('TableUser', primaryjoin='TableAccess.user_num == TableUser.num', backref='table_access')

    def __repr__(self):
        return f'<table_access {self.user_num},{self.access_flag},{self.access_time}>'

    def to_dict(self):
        return {
            'num': self.num,
            'user_num': self.user_num,
            'service_num': self.service_num,
            'access_flag': self.access_flag,
            'access_time': self.access_time,
            'result': self.result,
            'unregist': self.unregist,
            'will_fail': self.will_fail,
            'result_hand_left': self.result_hand_left,
            'value_hand_left': self.value_hand_left,
            'result_hand_right': self.result_hand_right,
            'value_hand_right': self.value_hand_right,
            'result_foot_left': self.result_foot_left,
            'value_foot_left': self.value_foot_left,
            'result_foot_right': self.result_foot_right,
            'value_foot_right': self.value_foot_right,
        }


class TableAttend(db.Model):
    __tablename__ = 'table_attend'

    num = Column(BigInteger, primary_key=True, info='记录序号，主键')
    user_num = Column(ForeignKey('table_user.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True,
                      info='人员序号，外键')
    attend_date = Column(Date, info='日期\n，只包括年月日')
    attend_time = Column(Numeric(10, 3), info='在岗时间')
    attend_time_require = Column(Numeric(10, 3), info='当天在岗时间要求，以小时为单位')
    access_times = Column(Integer, info='进出次数\n')
    access_times_limit = Column(Integer, info='进出次数限制')

    table_user = relationship('TableUser', primaryjoin='TableAttend.user_num == TableUser.num', backref='table_attends')

    def __repr__(self):
        return f'<table_attend {self.user_num}, {self.attend_date}, {self.attend_time}>'

    def to_dict(self):
        return {
            'num': self.num,
            'user_num': self.user_num,
            'attend_time': self.attend_time,
            'attend_date': self.attend_date,
            'attend_time_require': self.attend_time_require,
            'access_times': self.access_times,
            'access_times_limit': self.access_times_limit,
        }


class TableDepartment(db.Model):
    __tablename__ = 'table_department'

    num = Column(Integer, primary_key=True, info='部门序号、主键')
    department_name = Column(String(50), nullable=False, info='部门名', unique=True)

    t_table_department_position = Table(
        'table_department_position', metadata,
        Column('num', Integer, nullable=False, info='部门职位关系表序号、主键'),
        Column('department_num', ForeignKey('table_department.num', ondelete='CASCADE', onupdate='CASCADE'),
               nullable=False,
               index=True, info='部门序号、外键'),
        Column('position_num', ForeignKey('table_position.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
               index=True, info='职位序号、外键')
    )

    def __repr__(self):
        return f'<table_department {self.num},{self.department_name}>'

    def to_dict(self):
        return {
            'num': self.num,
            'department_name': self.department_name,
        }


class TablePosition(db.Model):
    __tablename__ = 'table_position'

    num = Column(Integer, primary_key=True, info='职位序号、主键')
    position_name = Column(String(50), nullable=False, info='职位名字', unique=True)

    def __repr__(self):
        return f'<table_position {self.num},{self.position_name}>'

    def to_dict(self):
        return {
            'num': self.num,
            'position_name': self.position_name,
        }


class TableDepartmentPosition(db.Model):
    __tablename__ = 'table_department_position'

    num = Column(Integer, primary_key=True, info='部门职位关系序号、主键')
    department_num = Column(ForeignKey('table_department.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                            index=True, info='部门序号、外键')
    position_num = Column(ForeignKey('table_position.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                          index=True, info='职位序号、外键')

    table_position = relationship('TablePosition',
                                  primaryjoin='TableDepartmentPosition.position_num == TablePosition.num',
                                  backref='table_department_position')
    table_department = relationship('TableDepartment',
                                    primaryjoin='TableDepartmentPosition.department_num == TableDepartment.num',
                                    backref='table_department_position')

    def __repr__(self):
        return f'<table_department_position {self.department_num},{self.position_num}>'

    def to_dict(self):
        return {
            'num': self.num,
            'department_num': self.department_num,
            'position_num': self.position_num,
        }


class TableService(db.Model):
    __tablename__ = 'table_service'

    num = Column(Integer, primary_key=True, info='设备序号,主键')
    service_id = Column(String(50, 'utf8mb4_0900_ai_ci'), nullable=False, info='设备编号', unique=True)
    service_name = Column(String(50, 'utf8mb4_0900_ai_ci'), nullable=False, info='设备名称', unique=True)
    test_part = Column(String(3), nullable=False, default='111', info='电阻测试的部分，默认111表示测试左手、右手和双脚')
    r_standard_num = Column(ForeignKey('table_r_standard.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                            index=True, info='电阻标准序号、外键')
    table_r_standard = relationship('TableRStandard',
                                    primaryjoin='TableService.r_standard_num == TableRStandard.num',
                                    backref='table_service')

    def __repr__(self):
        return f'<table_service {self.service_name}>'

    def to_dict(self):
        return {
            'num': self.num,
            'service_id': self.service_id,
            'service_name': self.service_name,
            'test_part': self.test_part,
            'r_standard_num': self.r_standard_num
        }


class TableRStandard(db.Model):
    __tablename__ = 'table_r_standard'

    num = Column(Integer, primary_key=True, info='序号,自增主键')
    r_name = Column(String(50, 'utf8mb4_0900_ai_ci'), nullable=False, info='标准名称')
    hand_left_min = Column(Numeric(10, 2), info='检测时左手下限阻值')
    hand_left_max = Column(Numeric(10, 2), info='检测时左手上限阻值')
    hand_right_min = Column(Numeric(10, 2), info='检测时右手下限阻值')
    hand_right_max = Column(Numeric(10, 2), info='检测时右手上限阻值')

    foot_left_min = Column(Numeric(10, 2), info='检测时左脚下限阻值')
    foot_left_max = Column(Numeric(10, 2), info='检测时左脚上限阻值')
    foot_right_min = Column(Numeric(10, 2), info='检测时右脚下限阻值')
    foot_right_max = Column(Numeric(10, 2), info='检测时右脚上限阻值')

    def __repr__(self):
        return f'<table_r_standard {self.r_name}>'

    def to_dict(self):
        return {
            'num': self.num,
            'r_name': self.r_name,
            'hand_left_min': self.hand_left_min,
            'hand_left_max': self.hand_left_max,
            'hand_right_min': self.hand_right_min,
            'hand_right_max': self.hand_right_max,

            'foot_left_min': self.foot_left_min,
            'foot_left_max': self.foot_left_max,
            'foot_right_min': self.foot_right_min,
            'foot_right_max': self.foot_right_max,
        }


class TableUserService(db.Model):
    __tablename__ = 'table_user_service'

    num = Column(BigInteger, primary_key=True, info='关系序号\n，主键')
    user_num = Column(ForeignKey('table_user.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True,
                      info='人员序号，外键')
    service_num = Column(ForeignKey('table_service.num', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                         index=True, info='设备序号\n，外键')

    table_service = relationship('TableService', primaryjoin='TableUserService.service_num == TableService.num',
                                 backref='table_user_services')
    table_user = relationship('TableUser', primaryjoin='TableUserService.user_num == TableUser.num',
                              backref='table_user_services')

    def __repr__(self):
        return f'<table_user_service {self.user_num},{self.service_num}>'

    def to_dict(self):
        return {
            'num': self.num,
            'user_num': self.user_num,
            'service_num': self.service_num,
        }
