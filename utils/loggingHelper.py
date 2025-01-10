import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta

# 日志配置
LOG_DIR = "logs"  # 日志目录
LOG_FILE = "app.log"  # 日志文件名称
RETENTION_DAYS = 14  # 日志保留天数


def setup_logging(app):
    """配置日志"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_file_path = os.path.join(LOG_DIR, LOG_FILE)
    # 使用 TimedRotatingFileHandler 生成每天一个日志文件
    handler = TimedRotatingFileHandler(
        log_file_path,
        when="midnight",  # 每天凌晨生成新日志文件
        interval=1,
        backupCount=30,  # 最多保留 30 天的日志
        encoding="utf-8"
    )
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)


def clean_old_logs():
    """清理过期日志"""
    now = datetime.now()
    for filename in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_time > timedelta(days=RETENTION_DAYS):
                os.remove(file_path)
