import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta

LOG_DIR = "logs"  # 日志目录
LOG_FILE = "app.log"  # 日志文件名称
RETENTION_DAYS = 14  # 日志保留天数

# 确保日志目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def get_log_handler():
    """
    配置每天生成一个新日志文件，并保留指定天数的日志
    """
    log_file_path = os.path.join(LOG_DIR, LOG_FILE)

    # 使用 TimedRotatingFileHandler 生成每日日志文件
    handler = TimedRotatingFileHandler(
        log_file_path,
        when="midnight",  # 每天凌晨生成新日志文件
        interval=1,  # 间隔 1 天
        backupCount=30,  # 最多保留 30 个文件 (文件的个数)
        encoding="utf-8"  # 编码格式
    )
    handler.suffix = "%Y-%m-%d"  # 日志文件名称添加日期后缀
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    return handler


def clean_old_logs():
    """
    清理超过 RETENTION_DAYS 的过期日志文件
    """
    now = datetime.now()
    for filename in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_time > timedelta(days=RETENTION_DAYS):
                os.remove(file_path)
                print(f"已清理过期日志文件: {file_path}")
