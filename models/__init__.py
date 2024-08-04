import datetime
import decimal
from typing import List, Optional

from sqlalchemy import BigInteger, DECIMAL, Date, ForeignKeyConstraint, Index, Integer, TIMESTAMP, text
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import db


# 生成models方法 sqlacodegen mysql+pymysql://root:root@localhost/edsystem > models.py


class TableService(db.Model):
    __tablename__ = 'table_service'

    num: Mapped[int] = mapped_column(Integer, primary_key=True, comment='设备序号,主键')
    service_id: Mapped[str] = mapped_column(VARCHAR(50), comment='设备编号')
    service_name: Mapped[str] = mapped_column(VARCHAR(50), comment='设备名称')

    table_access: Mapped[List['TableAccess']] = relationship('TableAccess', back_populates='table_service')
    table_user_service: Mapped[List['TableUserService']] = relationship('TableUserService',
                                                                        back_populates='table_service')

    def __repr__(self):
        return f'<table_service {self.service_name}>'

    def to_dict(self):
        return {
            'num': self.num,
            'service_id': self.service_id,
            'service_name': self.service_name,
        }


class TableUser(db.Model):
    __tablename__ = 'table_user'

    num: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='人员序号,主键')
    name: Mapped[str] = mapped_column(VARCHAR(50), comment='姓名')
    is_delete: Mapped[int] = mapped_column(TINYINT, server_default=text("'0'"), comment='0表示未删除\n,1表示已删除')
    employee_id: Mapped[Optional[str]] = mapped_column(VARCHAR(50), comment='工号')
    department: Mapped[Optional[str]] = mapped_column(VARCHAR(50), comment='部门')
    position: Mapped[Optional[str]] = mapped_column(VARCHAR(50), comment='职位')
    card_id: Mapped[Optional[str]] = mapped_column(VARCHAR(50), comment='卡号')
    pic_path: Mapped[Optional[str]] = mapped_column(VARCHAR(100), comment='照片,设置成路径')

    table_access: Mapped[List['TableAccess']] = relationship('TableAccess', back_populates='table_user')
    table_attend: Mapped[List['TableAttend']] = relationship('TableAttend', back_populates='table_user')
    table_user_service: Mapped[List['TableUserService']] = relationship('TableUserService', back_populates='table_user')

    def __repr__(self):
        return f'<table_user {self.name}>'

    def to_dict(self):
        return {
            'num': self.num,
            'employee_id': self.employee_id,
            'name': self.name,
            'department': self.department,
            'position': self.position,
            'card_id': self.card_id,
            'pic_path': self.pic_path,
            'is_delete': self.is_delete
        }


class TableAccess(db.Model):
    __tablename__ = 'table_access'
    __table_args__ = (
        ForeignKeyConstraint(['service_num'], ['table_service.num'], ondelete='CASCADE', onupdate='CASCADE',
                             name='service_num_access_foreign'),
        ForeignKeyConstraint(['user_num'], ['table_user.num'], ondelete='CASCADE', onupdate='CASCADE',
                             name='user_num_access_foreign'),
        Index('service_num_access_foreign', 'service_num'),
        Index('user_num_access_foreign', 'user_num')
    )

    num: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='记录序号num\n,主键')
    user_num: Mapped[int] = mapped_column(BigInteger, comment='人员序号num\n,外键')
    service_num: Mapped[int] = mapped_column(Integer, comment='设备序号num\n,外键')
    access_flag: Mapped[int] = mapped_column(TINYINT, comment='进出标志位，1或2，1表示进，2表示出')
    access_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, comment='进出时间accessTime')
    result: Mapped[int] = mapped_column(TINYINT, comment='员工静电测试总结果，1"合格"2"不合格"3"免测"4"未测"5"禁测"')
    unregist: Mapped[Optional[int]] = mapped_column(TINYINT,
                                                    comment='表示员工刷卡时（特殊的临时卡），是否已登记，未登记值为1，登记值为2')
    will_fail: Mapped[Optional[str]] = mapped_column(VARCHAR(10),
                                                     comment='标示员工的手环、静电鞋是否即将失效。 如000表示没有失效的\n第1位表示手环是否失效，0表示没有即将失效，1表示即将失效\n第2位表示左脚静电鞋是否失效，0表示没有即将失效，1表示即将失效\n第3位表示右脚静电鞋是否失效，0表示没有即将失效，1表示即将失效')
    result_hand_left: Mapped[Optional[int]] = mapped_column(TINYINT,
                                                            comment='左手测试结果，1"合格"2"不合格"3"免测"4"未测"5"禁测"')
    value_hand_left: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                       comment='左手测试实际阻值,单位:兆欧姆')
    result_hand_right: Mapped[Optional[int]] = mapped_column(TINYINT,
                                                             comment='右手测试结果，"合格""不合格""免测""未测""禁测"')
    value_hand_right: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                        comment='右手测试实际阻值,单位:兆欧姆')
    result_foot_left: Mapped[Optional[int]] = mapped_column(TINYINT,
                                                            comment='左脚测试结果，"合格""不合格""免测""未测""禁测"')
    value_foot_left: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                       comment='左脚测试实际阻值,单位:兆欧姆')
    result_foot_right: Mapped[Optional[int]] = mapped_column(TINYINT,
                                                             comment='右脚测试结果，"合格""不合格""免测""未测""禁测"')
    value_foot_right: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                        comment='右脚测试实际阻值,单位:兆欧姆')
    hand_left_min: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时左手下限阻值')
    hand_left_max: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时左手上限阻值')
    hand_right_min: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时右手下限阻值')
    hand_right_max: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时右手上限阻值')
    foot_left_min: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时左脚下限阻值')
    foot_left_max: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时左脚上限阻值')
    foot_right_min: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时右脚下限阻值')
    foot_right_max: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='检测时右脚上限阻值')

    table_service: Mapped['TableService'] = relationship('TableService', back_populates='table_access')
    table_user: Mapped['TableUser'] = relationship('TableUser', back_populates='table_access')

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
            'hand_left_min': self.hand_left_min,
            'hand_left_max': self.hand_left_max,
            'hand_right_min': self.hand_right_min,
            'hand_right_max': self.hand_right_max,
            'foot_left_min': self.foot_left_min,
            'foot_left_max': self.foot_left_max,
            'foot_right_min': self.foot_right_min,
            'foot_right_max': self.foot_right_max,
        }


# 有多余属性service_num，但是删除了会影响access页面
class TableAttend(db.Model):
    __tablename__ = 'table_attend'
    __table_args__ = (
        ForeignKeyConstraint(['user_num'], ['table_user.num'], ondelete='CASCADE', onupdate='CASCADE',
                             name='user_num_attend_foreign'),
        Index('user_num_attend_foreign', 'user_num')
    )

    num: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='记录序号，主键')
    user_num: Mapped[int] = mapped_column(BigInteger, comment='人员序号，外键')
    attend_date: Mapped[Optional[datetime.date]] = mapped_column(Date, comment='日期\n，只包括年月日')
    attend_time: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 3), comment='在岗时间')
    attend_time_require: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 3),
                                                                           comment='当天在岗时间要求，以小时为单位')
    access_times: Mapped[Optional[int]] = mapped_column(Integer, comment='进出次数\n')
    access_times_limit: Mapped[Optional[int]] = mapped_column(Integer, comment='进出次数限制')

    table_user: Mapped['TableUser'] = relationship('TableUser', back_populates='table_attend')

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


class TableUserService(db.Model):
    __tablename__ = 'table_user_service'
    __table_args__ = (
        ForeignKeyConstraint(['service_num'], ['table_service.num'], ondelete='CASCADE', onupdate='CASCADE',
                             name='service_num_relation_foreign'),
        ForeignKeyConstraint(['user_num'], ['table_user.num'], ondelete='CASCADE', onupdate='CASCADE',
                             name='user_num_relation_foreign'),
        Index('service_num_relation_foreign', 'service_num'),
        Index('user_num_relation_foreign', 'user_num')
    )

    num: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='关系序号\n，主键')
    user_num: Mapped[int] = mapped_column(BigInteger, comment='人员序号，外键')
    service_num: Mapped[int] = mapped_column(Integer, comment='设备序号\n，外键')

    table_service: Mapped['TableService'] = relationship('TableService', back_populates='table_user_service')
    table_user: Mapped['TableUser'] = relationship('TableUser', back_populates='table_user_service')

    def __repr__(self):
        return f'<table_user_service {self.user_num},{self.service_num}>'

    def to_dict(self):
        return {
            'num': self.num,
            'user_num': self.user_num,
            'service_num': self.service_num,
        }
