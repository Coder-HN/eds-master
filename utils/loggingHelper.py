import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from flask import request

# 日志配置
LOG_DIR = "logs"  # 日志目录
RETENTION_DAYS = 14  # 日志保留天数


def setup_logging(app):
    """配置日志"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file_path = os.path.join(LOG_DIR, f"{current_date}_app.log")
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


def setup_request_logging(app):
    """配置 werkzeug 的日志格式"""
    werkzeug_logger = logging.getLogger('werkzeug')
    handler = logging.StreamHandler()  # 输出到控制台
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    werkzeug_logger.addHandler(handler)
    werkzeug_logger.setLevel(logging.INFO)

    # 添加 Flask 自定义请求日志
    @app.before_request
    def log_request():
        method = request.method
        url = request.url
        client_ip = request.remote_addr
        werkzeug_logger.info(f"{client_ip} {method} {url}")
