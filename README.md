# 静电检测系统的后端：edsMaster
## 克隆代码
git clone https://gitee.com/Henning_HHN/eds-master.git
## 拉取最新代码
git pull https://gitee.com/Henning_HHN/eds-master.git

## 环境准备
事先安装好pip和python

```bash
pip install -r requirements.txt
```

## 启动项目

使用Flask服务器运行(处理并发事件能力弱)

```bash
python -m flask run
```

使用gevent服务器运行(高并发,低内存)

```bash
python app_run_gevent.py
```

在anaconda环境下则还需指定D:\CodeSupport\Anaconda\envs\env_311\python.exe -m flask run

