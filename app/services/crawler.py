import time
import traceback
from datetime import datetime

import pytz

from app.services import factory, _scheduler
from app.utils.logger import log


@_scheduler.scheduled_job('interval', id='crawler_logic', seconds=1800)
def crawlers_logic():
    retry_crawler = []

    timezone = pytz.timezone('Asia/Shanghai')
    now_time = datetime.now(timezone)
    date_str = now_time.strftime("%Y-%m-%d")

    for crawler_name, crawler in factory.items():
        try:
            news_list = crawler.fetch(date_str)
        except Exception as e:
            log.error("first time crawler %s error: %s" % (crawler_name, traceback.format_exc()))
            retry_crawler.append(crawler_name)
            continue

        if len(news_list) != 0:
            # db.insert_news(news_list)
            log.info(f"{crawler_name} fetch success, {len(news_list)} news fetched")
        else:
            retry_crawler.append(crawler_name)
            log.info(f"{crawler_name} fetch failed， 0 news fetched")

    log.info(f"left {len(retry_crawler)} sites， start second time crawler")
    for crawler_name in retry_crawler:
        crawler = factory[crawler_name]
        try:
            news_list = crawler.fetch(date_str)
            if len(news_list) != 0:
                # db.insert_news(news_list)
                log.info(f"{crawler_name} fetch success，{len(news_list)} news fetched")
            else:
                log.info(f"sencond time crawler {crawler_name} failed. 0 news fetched")
        except Exception as e:
            log.error("second time crawler %s error: %s" % (crawler_name, traceback.format_exc()))
            continue

    log.info("crawler finished: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
