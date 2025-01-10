import os
import logging
import inspect
from typing import Optional
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta

# 日志配置
LOG_DIR = "logs"  # 日志目录
RETENTION_DAYS = 14  # 日志保留天数
logger: Optional[logging.Logger] = None  # 全局日志记录器


# 配置日志
def setup_logging(app, cmd_print):
    global logger  # 声明全局 logger
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
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s"
    ))

    # 配置应用的日志记录器
    app.logger.setLevel(logging.INFO)

    if not cmd_print:  # 移除默认的 StreamHandler
        for handler_to_remove in app.logger.handlers:
            if isinstance(handler_to_remove, logging.StreamHandler):
                app.logger.removeHandler(handler_to_remove)

    app.logger.addHandler(handler)
    logger = app.logger  # 设置全局 logger 为 Flask 应用的 logger


def log_message(message, level='info'):
    """
    记录日志的通用函数
    :param level: 日志级别 ('debug', 'info', 'warning', 'error', 'critical')
    :param message: 要记录的消息内容
    """
    if logger is None:
        raise RuntimeError("日志系统未初始化!")
    # 动态获取调用者的模块名称
    caller_frame = inspect.stack()[1]
    module_name = inspect.getmodule(caller_frame[0]).__name__

    # 为每个模块动态创建记录器
    dynamic_logger = logging.getLogger(module_name)
    if level.lower() == 'debug':
        dynamic_logger.debug(message)
    elif level.lower() == 'info':
        dynamic_logger.info(message)
    elif level.lower() == 'warning':
        dynamic_logger.warning(message)
    elif level.lower() == 'error':
        dynamic_logger.error(message)
    elif level.lower() == 'critical':
        dynamic_logger.critical(message)
    else:
        raise ValueError(f"未知的日志级别: {level}")


def clean_old_logs():
    """清理过期日志"""
    now = datetime.now()
    for filename in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - file_time > timedelta(days=RETENTION_DAYS):
                os.remove(file_path)
