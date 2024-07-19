import datetime
import decimal
from typing import List, Optional
from sqlalchemy import BigInteger, DECIMAL, ForeignKeyConstraint, Index, Integer, TIMESTAMP, text
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
    table_attend: Mapped[List['TableAttend']] = relationship('TableAttend', back_populates='table_service')
    table_user_service: Mapped[List['TableUserService']] = relationship('TableUserService',
                                                                        back_populates='table_service')

    def __repr__(self):
        return f'<table_service {self.service_name}>'


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
    access_flag: Mapped[int] = mapped_column(TINYINT, comment='进出标志位flag')
    access_time: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, comment='进出时间accessTime')
    result: Mapped[int] = mapped_column(TINYINT, comment='员工静电测试总结果，0合格,1不合格,2免测,3未测,4禁测')
    result_hand: Mapped[Optional[int]] = mapped_column(TINYINT, comment='0合格,1不合格,2免测,3未测,4禁测')
    result_leftfoot: Mapped[Optional[int]] = mapped_column(TINYINT, comment='0合格,1不合格,2免测,3未测,4禁测')
    result_rightfoot: Mapped[Optional[int]] = mapped_column(TINYINT, comment='0合格,1不合格,2免测,3未测,4禁测')
    value_hand: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                  comment='员工手环测试实际阻值,单位:兆欧姆')
    value_leftfoot: Mapped[Optional[decimal.Decimal]] = mapped_column('value leftfoot', DECIMAL(10, 2),
                                                                      comment='员工左脚测试实际阻值,单位:兆欧姆')
    value_rightfoot: Mapped[Optional[decimal.Decimal]] = mapped_column('value rightfoot', DECIMAL(10, 2),
                                                                       comment='员工右脚测试实际阻值,单位:兆欧姆')
    hand_min: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                comment='手环测试通过标准下限阻值,单位:兆欧姆')
    hand_max: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                comment='手环测试通过标准上限阻值,单位:兆欧姆')
    foot_min: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                comment='脚底测试通过标准下限阻值,单位:兆欧姆')
    foot_max: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2),
                                                                comment='脚底测试通过标准上限阻值,单位:兆欧姆')
    will_fail: Mapped[Optional[str]] = mapped_column(VARCHAR(10),
                                                     comment='标示员工的手环、静电鞋是否即将失效。 如"000"表示没有失效的\n第1位表示手环是否失效，0表示没有即将失效，1表示即将失效\n第2位表示左脚静电鞋是否失效，0表示没有即将失效，1表示即将失效\n第3位表示右脚静电鞋是否失效，0表示没有即将失效，1表示即将失效')
    unregist: Mapped[Optional[int]] = mapped_column(TINYINT, comment='表示员工刷卡时，是否已登记，未登记值为1，登记值为0')

    table_service: Mapped['TableService'] = relationship('TableService', back_populates='table_access')
    table_user: Mapped['TableUser'] = relationship('TableUser', back_populates='table_access')

    def __repr__(self):
        return f'<table_access {self.user_num},{self.access_flag},{self.access_time}>'


class TableAttend(db.Model):
    __tablename__ = 'table_attend'
    __table_args__ = (
        ForeignKeyConstraint(['service_num'], ['table_service.num'], ondelete='CASCADE', onupdate='CASCADE',
                             name='service_num_attend_foreign'),
        ForeignKeyConstraint(['user_num'], ['table_user.num'], ondelete='CASCADE', onupdate='CASCADE',
                             name='user_num_attend_foreign'),
        Index('service_num_attend_foreign', 'service_num'),
        Index('user_num_attend_foreign', 'user_num')
    )

    num: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='记录序号，主键')
    user_num: Mapped[int] = mapped_column(BigInteger, comment='人员序号，外键')
    service_num: Mapped[int] = mapped_column(Integer, comment='设备序号，外键')
    attend_date: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, comment='日期\n')
    attend_time: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='在岗时间')
    require_attend_time: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2), comment='在岗时间要求\n')
    access_times: Mapped[Optional[int]] = mapped_column(Integer, comment='进出次数\n')

    table_service: Mapped['TableService'] = relationship('TableService', back_populates='table_attend')
    table_user: Mapped['TableUser'] = relationship('TableUser', back_populates='table_attend')

    def __repr__(self):
        return f'<table_attend {self.user_num}, {self.attend_date}, {self.attend_time}>'


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
