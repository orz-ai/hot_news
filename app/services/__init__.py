from apscheduler.schedulers.background import BackgroundScheduler

from app.services.sites.factory import CrawlerRegister

factory = CrawlerRegister().register()

_scheduler = BackgroundScheduler()
_scheduler.start()
