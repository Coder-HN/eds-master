from models import TableUser
from database import db


def get_all_users():
    return TableUser.query.all()


def get_user_by_id(user_id):
    return TableUser.query.filter_by(id=user_id).first()


def create_user(name):
    new_user = TableUser(name=name, is_delete=0)
    db.session.add(new_user)
    db.session.commit()
    return new_user
