from gevent import pywsgi
from app import create_app
from scheduler_internet import start_internet_asks  # 导入定时任务

# 创建 Flask 应用
myapp = create_app(debug=True)

if __name__ == '__main__':
    start_internet_asks()  # 启动定时任务
    # 配置并运行 gevent WSGI 服务器
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), myapp, spawn=100)
    print("服务器已启动，监听地址：http://127.0.0.1:5000")
    server.serve_forever()
