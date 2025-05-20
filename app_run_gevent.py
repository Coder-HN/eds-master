from gevent import pywsgi
from app import create_app
import sys
import os

if __name__ == '__main__':
    # 创建 Flask 应用
    myapp = create_app(cmd_print=True)
    myapp.debug = True  # 设置调试模式
    # 禁用标准输出
    # sys.stderr = open(os.devnull, "w")
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), myapp, spawn=100)  # 配置并运行 gevent WSGI 服务器
    server.serve_forever()
