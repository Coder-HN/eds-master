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
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S GMT",  # 原始格式，保留备用
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None  # 全部解析失败


def parse_datetime_detail(date_str):
    """
    解析前端传来的“YYYY-MM-DD HH:mm”格式时间，设为北京时间。
    """
    try:
        # 先按前端格式解析为 datetime 对象（无时区）
        dt_naive = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

        # 设为北京时间（Asia/Shanghai）
        china_tz = pytz.timezone("Asia/Shanghai")
        dt_localized = china_tz.localize(dt_naive)
        return dt_localized
    except ValueError:
        return None


def get_start_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_end_of_day(dt):
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_date_by_timestamp(timestamp):
    date_only = timestamp.date()
    return date_only
