# 与云端数据库进行交互
from apscheduler.schedulers.background import BackgroundScheduler
from router.router_internet import update_cloud_userinfo_to_local, update_local_access_to_cloud
from utils.loggingHelper import clean_old_logs


# 同步云端用户信息数据
def update_local_userinfo():
    update_cloud_userinfo_to_local()


# 本地进出记录同步到云端
def sync_access_to_cloud():
    update_local_access_to_cloud()


# 配置定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(update_local_userinfo, 'cron', hour=0, minute=0)  # 每天 0:00 定时同步用户数据
scheduler.add_job(sync_access_to_cloud, 'interval', minutes=20)  # 每隔20分钟一次,更新云端数据库进出记录
scheduler.add_job(clean_old_logs, 'cron', hour=0, minute=0)  # 每天0点执行日志清理


def start_scheduler():
    scheduler.start()
    print("[Scheduler] 定时任务已启动")
