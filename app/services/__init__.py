from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
import pytz

from app.services.sites.factory import CrawlerRegister
from app.utils.logger import log
from app.core.config import get_scheduler_config

# 创建爬虫工厂
factory = CrawlerRegister().register()

# 获取调度器配置
scheduler_config = get_scheduler_config()

# 配置调度器
jobstores = {
    'default': MemoryJobStore()
}

executors = {
    'default': ThreadPoolExecutor(scheduler_config.thread_pool_size),
    'processpool': ProcessPoolExecutor(scheduler_config.process_pool_size)
}

job_defaults = {
    'coalesce': scheduler_config.coalesce,
    'max_instances': scheduler_config.max_instances,
    'misfire_grace_time': scheduler_config.misfire_grace_time,
}

# 创建并配置调度器
_scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=pytz.timezone(scheduler_config.timezone)
)

# 启动调度器
_scheduler.start()

log.info(f"Scheduler started with timezone: {scheduler_config.timezone}")
