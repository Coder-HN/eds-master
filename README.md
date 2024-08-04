部署方式
* 安装pip和python
* 安装依赖
  `pip install -r requirements.txt`




运行方式
(在anaconda环境下则还需指定D:\CodeSupport\Anaconda\envs\env_311\python.exe -m flask run)
* 使用Flask服务器运行(处理并发事件能力弱)
  `python -m flask run`
* 使用gevent服务器运行(高并发,低内存)
  `python app_run_gevent.py`

