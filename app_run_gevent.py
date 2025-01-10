from gevent import pywsgi
from app import create_app

if __name__ == '__main__':
    # 创建 Flask 应用
    myapp = create_app()
    myapp.debug = False  # 设置调试模式
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), myapp, spawn=100)  # 配置并运行 gevent WSGI 服务器
    # TODO
    print("服务器已启动，监听地址：http://127.0.0.1:5000")
    myapp.logger.info("服务器已启动，监听地址：http://127.0.0.1:5000")
    server.serve_forever()
