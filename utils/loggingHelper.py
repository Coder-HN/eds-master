import logging
from functools import wraps
from flask import current_app


def setup_logging(app):
    # 设置日志级别
    app.logger.setLevel(logging.INFO)

    # 创建一个文件处理器，并设置其日志格式
    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))

    # 将处理器添加到 Flask 的 logger
    app.logger.addHandler(file_handler)


def log_function_call(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        current_app.logger.info(f"Function called: {f.__name__}")
        return f(*args, **kwargs)

    return wrapped


def decorate_blueprint(bp):
    for endpoint, func in list(bp.view_functions.items()):
        if not getattr(func, 'is_logged', False):  # 防止重复装饰
            bp.deferred_functions[endpoint] = log_function_call(func)
            setattr(bp.deferred_functions[endpoint], 'is_logged', True)
