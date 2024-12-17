from gevent import pywsgi
from app import create_app
from scheduler_internet import start_scheduler  # 导入定时任务
from utils.loggingHelper import get_log_handler

# 创建 Flask 应用
myapp = create_app()

if __name__ == '__main__':
    # debug模式
    myapp.debug = False
    # 配置日志
    myapp.logger.addHandler(get_log_handler())
    start_scheduler()  # 启动定时任务
    # 配置并运行 gevent WSGI 服务器
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), myapp, spawn=100)
    print("服务器已启动，监听地址：http://127.0.0.1:5000")
    server.serve_forever()
