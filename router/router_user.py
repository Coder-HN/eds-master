from flask import Blueprint, jsonify, make_response, request, current_app

from config import Config
from mapper import UserMapper, ServiceMapper, AccessMapper, AttendMapper
from models import TableAccess, TableAttend

from utils import timeHelper, testResistanceHelper

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


# 测试失败后在规定时间内再次测试接口
@user.route('/test_user_r', methods=['GET'])
def test_user_r():
    print("重新测试阻值中--------------------------------------------------")
    r = testResistanceHelper.get_r()
    hand_left_min = Config.HAND_LEFT_MIN
    hand_left_max = Config.HAND_LEFT_MAX
    hand_right_min = Config.HAND_RIGHT_MIN
    hand_right_max = Config.HAND_RIGHT_MAX
    foot_left_min = Config.FOOT_LEFT_MIN
    foot_left_max = Config.FOOT_LEFT_MAX
    foot_right_min = Config.FOOT_RIGHT_MIN
    foot_right_max = Config.FOOT_RIGHT_MAX
    result = False
    service_id, value_hand_left, value_hand_right, value_foot_left, value_foot_right = None, None, None, None, None
    result_hand_left = 2
    result_hand_right = 2
    result_foot_left = 2
    result_foot_right = 2
    if r is not None:
        service_id, value_hand_left, value_hand_right, value_foot_left, value_foot_right = r
        print("service_id:", service_id)
        if hand_left_min <= value_hand_left <= hand_left_max:
            result_hand_left = 1
        if hand_right_min <= value_hand_right <= hand_right_max:
            result_hand_right = 1
        if foot_left_min <= value_foot_left <= foot_left_max:
            result_foot_left = 1
        if foot_right_min <= value_foot_right <= foot_right_max:
            result_foot_right = 1
        if result_hand_left == 1 and result_hand_right == 1 and result_foot_left == 1 and result_foot_right == 1:
            result = True
    result_num = 2
    if result:
        result_num = 1
    set_data = {
        'result_num': result_num,
        'value_hand_left': value_hand_left,
        'value_hand_right': value_hand_right,
        'value_foot_left': value_foot_left,
        'value_foot_right': value_foot_right,
        'result_hand_left': result_hand_left,
        'result_hand_right': result_hand_right,
        'result_foot_left': result_foot_left,
        'result_foot_right': result_foot_right,
    }
    print(set_data)
    if result:
        print("开门中--------------------------------------------------")
        testResistanceHelper.open_door()
    return jsonify({'data': set_data}), 200


@user.route('/addAccess', methods=['POST'])
def add_access():
    data = request.get_json()
    access_flag = data.get('access_flag')
    user_num = data.get('user_num')
    service_id = data.get('service_id')
    card_id = data.get('card_id')
    service = ServiceMapper.get_service_by_id(service_id)
    service_num = service.num
    # TODO will_fail，unregist功能未完善
    will_fail = "000"
    unregist = 1  # 需要检查卡号是不是特殊卡号
    access_time = timeHelper.get_now_time()
    new_access = TableAccess()
    if access_flag == 1:
        value_hand_left = data.get('value_hand_left')
        value_hand_right = data.get('value_hand_right')
        value_foot_left = data.get('value_foot_left')
        value_foot_right = data.get('value_foot_right')
        hand_left_min = Config.HAND_LEFT_MIN
        hand_left_max = Config.HAND_LEFT_MAX
        hand_right_min = Config.HAND_RIGHT_MIN
        hand_right_max = Config.HAND_RIGHT_MAX
        foot_left_min = Config.FOOT_LEFT_MIN
        foot_left_max = Config.FOOT_LEFT_MAX
        foot_right_min = Config.FOOT_RIGHT_MIN
        foot_right_max = Config.FOOT_RIGHT_MAX
        if hand_left_min <= value_hand_left <= hand_left_max:
            result_hand_left = 1
        else:
            result_hand_left = 2
        if hand_right_min <= value_hand_right <= hand_right_max:
            result_hand_right = 1
        else:
            result_hand_right = 2
        if foot_left_min <= value_foot_left <= foot_left_max:
            result_foot_left = 1
        else:
            result_foot_left = 2
        if foot_right_min <= value_foot_right <= foot_right_max:
            result_foot_right = 1
        else:
            result_foot_right = 2
        if result_hand_left == 1 and result_hand_right == 1 and result_foot_left == 1 and result_foot_right == 1:
            result = 1
        else:
            result = 2
        new_access.result = result
        new_access.result_hand_left = result_hand_left
        new_access.result_hand_right = result_hand_right
        new_access.result_foot_left = result_foot_left
        new_access.result_foot_right = result_foot_right
        new_access.value_hand_left = value_hand_left
        new_access.value_hand_right = value_hand_right
        new_access.value_foot_left = value_foot_left
        new_access.value_foot_right = value_foot_right
    new_access.user_num = user_num
    new_access.service_num = service_num
    new_access.access_flag = access_flag
    new_access.access_time = access_time
    new_access.unregist = unregist
    new_access.will_fail = will_fail
    try:
        AccessMapper.add_access(new_access)
        if access_flag == 2:
            update_attend_table(access_time, card_id)
    except Exception as e:
        return jsonify({'error': e}), 500
    return make_response('', 200)


def update_attend_table(access_time, card_id):
    try:
        # 求这次进出的在岗时间
        _user = UserMapper.get_users_by_multiple_conditions(card_id=card_id)[0]
        access_enter = AccessMapper.get_access_enter_by_leave(_user.num)
        time_difference = access_time - timeHelper.get_utc_time(access_enter.access_time)
        # 将时间差转换为以小时为单位的小数值
        hours_difference = time_difference.total_seconds() / 3600
        # 检查是否存在出勤记录
        access_date = timeHelper.get_date_by_timestamp(access_time)
        attend = AttendMapper.get_attend_by_user_num_attend_date(_user.num, access_date)
        if attend is not None:
            AttendMapper.update_attend(attend.num, hours_difference)
        else:
            new_attend = TableAttend()
            new_attend.user_num = _user.num
            new_attend.attend_date = access_date
            new_attend.attend_time = hours_difference
            new_attend.attend_time_require = Config.ATTEND_TIME_REQUIRE
            new_attend.access_times = 1
            new_attend.access_times_limit = Config.ACCESS_TIMES_LIMIT
            AttendMapper.add_attend(new_attend)
    except Exception as e:
        return jsonify({'error': e}), 500
    return True
