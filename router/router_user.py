from flask import Flask, Blueprint, redirect, url_for, request
import json

"""
创建一个名user的蓝图,并在其中定义路由
/api
门禁处
/user/index：播放ESD检测的步骤视频
/user/detect：检测开始，动态更新是否符合校验要求
/user/detect/warn：通过查询进出记录及上岗时间，做出上岗时间，进出次数的预警
/user/detect/pass：检测成功通行
/user/detect/fail：检测失败不予通行
"""
user = Blueprint('user', __name__, url_prefix='/api/user')


@user.route('/login', methods=['POST'])
def user_login():
    # 获取前端json数据
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username == 'admin' and password == 'hhn':
        print("login success")
        global user_info
        user_info = json.loads('{"username": "admin"}')
        token = username + password
        return json.dumps({'status': 'ok', 'type': username, 'currentAuthority': token})
    else:
        print("login fail")
        return json.dumps({'status': 'failed'})


@user.route('/register')
def user_register():
    return 'Hello, World! This is the register page.'
