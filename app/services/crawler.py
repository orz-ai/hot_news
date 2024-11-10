import time
import traceback
from datetime import datetime

import pytz

from app.core import db
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
            log.info(f"{crawler_name}爬取成功，共爬取{len(news_list)}条新闻")
        else:
            retry_crawler.append(crawler_name)
            log.info(f"{crawler_name}爬取失败，爬取到0条新闻")

    log.info(f"剩余爬取{len(retry_crawler)}个网站，开始重试爬取")
    for crawler_name in retry_crawler:
        crawler = factory[crawler_name]
        try:
            news_list = crawler.fetch(date_str)
            if len(news_list) != 0:
                # db.insert_news(news_list)
                log.info(f"{crawler_name}爬取成功，共爬取{len(news_list)}条新闻")
            else:
                log.info(f"第二次重试{crawler_name}爬取失败，爬取到0条新闻")
        except Exception as e:
            log.error("second time crawler %s error: %s" % (crawler_name, traceback.format_exc()))
            continue

    log.info("爬取结束: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
