from flask import Flask, Blueprint, request, send_file, make_response
import os
import json
import service
import numpy as np
from database import db
import pandas as pd

from mapper import UserMapper

"""
功能主页
创建一个名admin的蓝图,并在其中定义路由
管理处
进出记录查询
/admin/searchAccess：查询进出记录，按照 姓名，工号，部门进行数据查询，包括进出时间，进出记录
员工考勤查询
/admin/searchAttend：查询日常考勤
员工管理
/admin/manageUser：查询人员信息；上传人员数据、导入数据库；导出数据表；导出数据库；
设备管理
/admin/manageService：上传设备信息；设置设备名称，上岗时间，进出预警时间；静电检测板的标定
"""
admin = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin.route('/manageUser/getAllUsers', methods=['GET'])
def get_all_users():
    all_users = UserMapper.get_all_users()
    print(all_users)
    return json.dumps("all_users")


# 上传患者数据csv
@admin.route('/upload', methods=['POST'])
def upload_txt():
    file = request.files['file']
    file.save('./uploads/临时保存.csv')
    try:
        train_x = np.loadtxt('./uploads/临时保存.csv', delimiter=",")
        print("上传文件维度为：", train_x.shape)
    except FileNotFoundError:
        print("文件上传失败")
        return json.dumps({'status': "fail"})
    return json.dumps({'status': "success"})


# 获取KNN结果
@admin.route('/getKNN', methods=['POST'])
def get_knn_list():
    search_table = ""
    # 获取前端json数据
    data = request.get_json()
    k = data.get('k')
    model_type = data.get('modelType')
    print(f"前端数据k={k},model_type={model_type}")


# 获取待检索患者特征向量
@admin.route('/download_search', methods=['GET'])
def download_search():
    response = make_response(send_file("", as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename=search_data.csv"
    return response


# 获取相似病例患者数据
@admin.route('/download_searched', methods=['GET'])
def download_searched():
    response = make_response(send_file("", as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename=searched_data.csv"
    return response
