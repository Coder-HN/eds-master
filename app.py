import threading
from flask import Flask, jsonify, abort
import traceback
from flask_socketio import SocketIO
from werkzeug.exceptions import HTTPException
from config import Config
from database import db
from router.router_admin_access import searchAccess
from router.router_admin_attend import searchAttend
from router.router_admin_manager_department import manageDepartment
from router.router_admin_manager_service import manageService
from router.router_admin_manager_user import manageUser
from router.router_user import user
from router.router_internet import inter
from scheduler_internet import start_scheduler_with_context
from thread_tasks import monitor_entrance, monitor_exit, manage_system, electric_control
from utils.loggingHelper import setup_logging, clean_old_logs


def create_app(config_class=Config):
    # 创建 Flask 应用
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 日志配置
    setup_logging(app)
    clean_old_logs()
    # 添加全局异常处理
    register_error_handlers(app)

    # 初始化 SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
    # TODO
    print("SocketIO 初始化成功" if socketio else "SocketIO 初始化失败")
    app.logger.info("SocketIO 初始化成功" if socketio else "SocketIO 初始化失败")

    # 启动多线程任务
    def start_threads():
        threading.Thread(target=monitor_entrance, args=(Config.test_enter_card_port, Config.default_baud_rate),
                         daemon=True).start()
        threading.Thread(target=monitor_exit, args=(Config.test_leave_card_port, Config.default_baud_rate),
                         daemon=True).start()
        threading.Thread(target=manage_system, args=(socketio,), daemon=True).start()
        threading.Thread(target=electric_control, args=(Config.test_r_port, Config.default_baud_rate, app),
                         daemon=True).start()

    start_threads()

    # 启动定时任务
    start_scheduler_with_context()

    # 初始化数据库
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # 注册蓝图
    blueprints = [user, inter, manageUser, manageDepartment, manageService, searchAccess, searchAttend]
    for bp in blueprints:
        app.register_blueprint(bp)

    @app.route('/test_exception')
    def test_exception():
        # 人为触发未处理的异常
        1 / 0

    @app.route('/test_http_exception')
    def test_http_exception():
        # 人为触发 HTTP 异常
        abort(404)  # 模拟页面未找到

    return app


# 注册全局异常处理器
def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        """
        捕获未处理的异常并记录详细日志
        """
        error_trace = traceback.format_exc()  # 获取详细的错误堆栈信息
        app.logger.error("Unhandled Exception occurred")
        app.logger.error(f"错误类型: {type(e).__name__}")
        app.logger.error(f"错误信息: {str(e)}")
        app.logger.error(f"错误堆栈信息:\n{error_trace}")

        # 返回标准化的 JSON 错误响应
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "details": "An unexpected error occurred. Please contact support."
        }), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """
        捕获 HTTP 异常并记录详细日志
        """
        error_trace = traceback.format_exc()  # 获取详细的错误堆栈信息
        app.logger.error("HTTP Exception occurred")
        app.logger.error(f"HTTP 错误: {e.name}")
        app.logger.error(f"HTTP 状态码: {e.code}")
        app.logger.error(f"错误信息: {e.description}")
        app.logger.error(f"错误堆栈信息:\n{error_trace}")

        # 返回标准化的 JSON 错误响应
        return jsonify({
            "error": e.name,
            "message": e.description,
            "details": "A request error occurred. Please verify the request and try again."
        }), e.code
