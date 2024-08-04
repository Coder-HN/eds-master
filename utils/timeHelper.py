from datetime import datetime, timezone, timedelta
import pytz


def get_utc_time(naive_time):
    naive_time.replace(tzinfo=timezone.utc)  # 获取UTC时间
    local_tz = pytz.timezone('Asia/Shanghai')  # 获取本地时区,Beijing有点问题
    local_time = naive_time.astimezone(local_tz)  # 转换为本地时间
    return local_time


def get_now_time():
    utc_time = datetime.utcnow().replace(tzinfo=timezone.utc)  # 获取UTC时间
    local_tz = pytz.timezone('Asia/Shanghai')  # 获取本地时区,Beijing有点问题
    local_time = utc_time.astimezone(local_tz)  # 转换为本地时间
    return local_time


def parse_datetime(date_str):
    date_format = "%a, %d %b %Y %H:%M:%S GMT"
    try:
        dt = datetime.strptime(date_str, date_format)
        dt = dt.replace(tzinfo=pytz.UTC)  # 设置时区信息为 UTC
        return dt + timedelta(days=1)
    except ValueError:
        return None


def get_start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day(dt):
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_date_by_timestamp(timestamp):
    date_only = timestamp.date()
    return date_only
