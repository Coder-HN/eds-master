from flask import Blueprint, jsonify, make_response, request

from config import Config
from mapper import UserMapper, ServiceMapper, AccessMapper, AttendMapper, RStandardMapper
from models import TableAccess, TableAttend
from thread_tasks import add_task_standard_r

from utils import timeHelper

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
        r_standard = RStandardMapper.get_r_standard_by_num(service.r_standard_num)
        hand_left_min = float(r_standard.hand_left_min)
        hand_left_max = float(r_standard.hand_left_max)
        hand_right_min = float(r_standard.hand_right_min)
        hand_right_max = float(r_standard.hand_right_max)
        foot_left_min = float(r_standard.foot_left_min)
        foot_left_max = float(r_standard.foot_left_max)
        foot_right_min = float(r_standard.foot_right_min)
        foot_right_max = float(r_standard.foot_right_max)
        result = 1
        if value_hand_left != -1 and hand_left_min <= value_hand_left <= hand_left_max:
            result_hand_left = 1
        else:
            result_hand_left = 2
            result = 2

        if value_hand_right != -1 and hand_right_min <= value_hand_right <= hand_right_max:
            result_hand_right = 1
        else:
            result_hand_right = 2
            result = 2
        if value_foot_left != -1 and foot_left_min <= value_foot_left <= foot_left_max:
            result_foot_left = 1
        else:
            result_foot_left = 2
            result = 2
        if value_foot_right != -1 and foot_right_min <= value_foot_right <= foot_right_max:
            result_foot_right = 1
        else:
            result_foot_right = 2
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
        _user = UserMapper.get_user_by_card_id(card_id=card_id)
        access_enter = AccessMapper.get_access_enter_by_leave(_user.num)
        if access_enter is not None:
            print(access_enter)
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
        else:
            print(f"{_user}人员无进门记录，但是存在出门记录")
    except Exception as e:
        return jsonify({'error': e}), 500
    return True


# 校准电阻
@user.route('/standard_r', methods=['POST'])
def do_standard_r():
    print("校准阻值中--------------------------------------------------")
    data = request.json  # 如果使用 JSON 形式
    test_part = data.get('testPart')  # 1~4
    test_step = data.get('testStep')  # 1~8
    print(f"test_part = {test_part}")
    print(f"test_step = {test_step}")
    if add_task_standard_r(test_part, test_step):
        return jsonify(), 200
    else:
        return jsonify(), 201
