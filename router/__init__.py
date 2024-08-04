from flask import Blueprint, redirect, url_for

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return redirect(url_for('searchAccess.getAllAccess'))
