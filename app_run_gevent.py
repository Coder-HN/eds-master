from gevent import pywsgi
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.debug = True
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), app, spawn=100)  # 调整 spawn 数量
    server.serve_forever()
